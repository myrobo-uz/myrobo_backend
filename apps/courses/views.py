import io
import secrets
import string
from datetime import timedelta

from django.core.cache import cache
from django.db import connections, transaction
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from apps.users.models import User
from apps.users.authentication import CustomJWTAuthentication

from .models import (
    Company,
    Course,
    CoursePlan,
    CourseType,
    Lesson,
    LessonProgress,
    PromoCode,
    UserCoursePurchase,
    UserSubscription,
    LessonTask,
    SubmissionStatus,
    Submission,
)
from .permission import IsAdminUser, IsCourseSubscribed, IsLessonAccessible
from .serializers import (
    CompleteLessonResponseSerializer,
    CourseDetailSerializer,
    SubmissionResultSerializer,
    CoursePlanSerializer,
    CourseListSerializer,
    LessonDetailSerializer,
    SubmissionCreateSerializer,
    PurchaseCourseRequestSerializer,
    UserCoursePurchaseSerializer,
    UserSubscriptionSerializer,
    CodeSubmissionSerializer,
)
from .services.compilator import judge_submission
from .utils import get_course_progress


@extend_schema(tags=["CourseTypes"], summary="Kurs turlari ro'yxati va yaratish")
class CourseTypeListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = CourseType.objects.all()
        from .serializers import CourseTypeSerializer
        return Response(CourseTypeSerializer(qs, many=True).data)




@extend_schema(tags=["Courses"], summary="Kurslar ro'yxati")
class CourseListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseListSerializer
    queryset = Course.objects.select_related("course_type").prefetch_related("teachers")


@extend_schema(tags=["Courses"], summary="Kurs tafsiloti")
class CourseDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseDetailSerializer
    queryset = Course.objects.select_related("course_type").prefetch_related(
        "teachers", "modules__lessons"
    )
    lookup_field = "slug"

    def _increment_views(self, course, request):
        if request.user and hasattr(request.user, "id"):
            identifier = f"user_{request.user.id}"
        else:
            identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        cache_key = f"course_view_{course.id}_{identifier}"
        if not cache.get(cache_key):
            Course.objects.filter(pk=course.pk).update(views=course.views + 1)
            cache.set(cache_key, True, timeout=60 * 60 * 24)

    def retrieve(self, request, *args, **kwargs):
        course = self.get_object()
        self._increment_views(course, request)

        data = self.get_serializer(course).data
        is_subscribed = False

        if request.user.is_authenticated:
            is_subscribed = course.user_has_access(request.user)

        if not is_subscribed:
            for module in data["modules"]:
                module["lessons"] = []

        data["progress"] = get_course_progress(request.user, course) if request.user.is_authenticated else 0
        data["is_subscribed"] = is_subscribed

        return Response(data)


@extend_schema(tags=["Courses"], summary="Dars tafsiloti")
class LessonDetailAPIView(RetrieveAPIView):
    permission_classes = [IsLessonAccessible]
    serializer_class = LessonDetailSerializer
    queryset = Lesson.objects.prefetch_related("tasks__test_cases")
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        return Response(self.get_serializer(lesson).data)


@extend_schema(
    tags=["Courses"],
    summary="Darsni yakunlash",
    request=None,
    responses={200: CompleteLessonResponseSerializer},
)
class CompleteLessonAPIView(APIView):
    permission_classes = [IsCourseSubscribed]

    def post(self, request, slug):
        lesson = Lesson.objects.get(slug=slug)
        obj, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        obj.is_completed = True
        obj.completed_at = timezone.now()
        obj.save(update_fields=["is_completed", "completed_at", "updated_at"])
        return Response({"status": "completed", "lesson": lesson.slug})


@extend_schema(
    tags=["Courses"],
    summary="Kurs yoki obuna sotib olish",
    request=PurchaseCourseRequestSerializer,
)
class PurchaseCourseAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]

    @transaction.atomic
    def post(self, request, slug):
        from .tasks import (
            send_course_invite_links_task,
            send_subscription_invite_links_task,
        )

        user_id = request.auth.payload.get("user_id")
        user = User.objects.select_for_update().get(id=user_id)
        course = Course.objects.get(slug=slug)

        purchase_type = request.data.get("purchase_type")
        if purchase_type not in ("course", "subscription"):
            raise ValidationError("purchase_type 'course' yoki 'subscription' bo'lishi kerak")

        promo_code_str = request.data.get("promo_code")
        promo = None
        if promo_code_str:
            promo = PromoCode.objects.filter(code=promo_code_str).first()
            if not promo or not promo.is_valid():
                raise ValidationError("Promo kod yaroqsiz")

        if purchase_type == "course":
            if UserCoursePurchase.objects.filter(user=user, course=course).exists():
                raise ValidationError("Siz bu kursni allaqachon sotib olgansiz")

            price = course.price
            if promo:
                price = price - (price * promo.discount_percent / 100)
            if user.balance < price:
                raise ValidationError("Yetarli balans yo'q")

            if promo:
                promo.used_count += 1
                promo.save(update_fields=["used_count"])

            user.balance -= price
            user.save(update_fields=["balance"])

            UserCoursePurchase.objects.create(
                user=user,
                course=course,
                promo_code=promo,
                original_price=course.price,
                final_price=price,
            )

            if user.telegram_id:
                transaction.on_commit(
                    lambda: send_course_invite_links_task.delay(
                        telegram_id=user.telegram_id, course_id=str(course.id)
                    )
                )

            return Response({
                "status": "success",
                "purchase_type": "individual_course",
                "course": course.slug,
                "paid": float(price),
                "balance": float(user.balance),
            })

        plan_id = request.data.get("plan_id")
        if not plan_id:
            raise ValidationError("Subscription uchun plan_id talab qilinadi")

        plan = CoursePlan.objects.filter(id=plan_id, is_active=True).first()
        if not plan:
            raise ValidationError("Noto'g'ri plan")
        if not plan.courses.filter(id=course.id).exists():
            raise ValidationError("Bu kurs shu rejada mavjud emas")

        active_sub = UserSubscription.objects.filter(
            user=user,
            plan=plan,
            is_active=True,
            expires_at__gt=timezone.now(),
        ).first()
        if active_sub:
            raise ValidationError(
                f"Siz bu rejaga allaqachon obuna bo'lgansiz. "
                f"Muddati: {active_sub.expires_at.strftime('%d.%m.%Y')}"
            )

        price = plan.price
        if promo:
            price = price - (price * promo.discount_percent / 100)
        if user.balance < price:
            raise ValidationError("Yetarli balans yo'q")

        if promo:
            promo.used_count += 1
            promo.save(update_fields=["used_count"])

        user.balance -= price
        user.save(update_fields=["balance"])

        expires_at = timezone.now() + timedelta(days=plan.duration_days)
        UserSubscription.objects.create(
            user=user,
            plan=plan,
            promo_code=promo,
            original_price=plan.price,
            final_price=price,
            expires_at=expires_at,
            is_active=True,
        )

        if user.telegram_id:
            transaction.on_commit(
                lambda: send_subscription_invite_links_task.delay(
                    telegram_id=user.telegram_id, plan_id=str(plan.id)
                )
            )

        return Response({
            "status": "success",
            "purchase_type": "subscription",
            "plan": plan.title,
            "duration_days": plan.duration_days,
            "expires_at": expires_at.isoformat(),
            "paid": float(price),
            "balance": float(user.balance),
        })


@extend_schema(tags=["Courses"], summary="Mening obunalarim")
class UserSubscriptionsListAPIView(ListAPIView):
    serializer_class = UserSubscriptionSerializer
    authentication_classes = [CustomJWTAuthentication]

    def get_queryset(self):
        user_id = self.request.auth.payload.get("user_id")
        return UserSubscription.objects.filter(user_id=user_id).select_related("plan", "promo_code")


@extend_schema(tags=["Courses"], summary="Mening sotib olgan kurslarim")
class UserCoursePurchasesListAPIView(ListAPIView):
    serializer_class = UserCoursePurchaseSerializer
    authentication_classes = [CustomJWTAuthentication]

    def get_queryset(self):
        user_id = self.request.auth.payload.get("user_id")
        return UserCoursePurchase.objects.filter(user_id=user_id).select_related(
            "course", "promo_code"
        )


class LessonTaskSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_slug):
        lesson = get_object_or_404(Lesson, slug=lesson_slug)

        if not lesson.module.course.user_has_access(request.user):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        tasks = lesson.tasks.all().values("id", "title", "description", "statement")
        return Response(list(tasks))

    def post(self, request, lesson_slug):
        lesson = get_object_or_404(Lesson, slug=lesson_slug)

        if not lesson.module.course.user_has_access(request.user):
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = get_object_or_404(LessonTask, id=request.data.get("task_id"), lesson=lesson)

        code = serializer.validated_data["code"]
        language = serializer.validated_data["language"]

        # Guard: ensure the task has test cases configured in the compilator
        if not task.test_cases.exists():
            return Response(
                {"detail": "This task has no test cases configured yet."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        submission = Submission.objects.create(
            task=task,
            user=request.user,
            code=code,
            language=language,
            status=SubmissionStatus.PENDING,
        )

        connections.close_all()

        compilator_result = judge_submission(task, code, language)
        final_verdict = compilator_result.get("finalVerdict", "")

        if final_verdict == "Accepted":
            submission.status = SubmissionStatus.ACCEPTED
        elif final_verdict == "WrongAnswer":
            submission.status = SubmissionStatus.WRONG
        else:
            submission.status = SubmissionStatus.ERROR

        submission.result = compilator_result
        submission.save(update_fields=["status", "result"])

        return Response(
            {
                "submission_id": submission.id,
                "status": submission.status,
                "result": compilator_result,
            },
            status=status.HTTP_200_OK,
        )

class CoursePlanListAPIView(APIView):
    def get(self, request):
        plans = CoursePlan.objects.prefetch_related("courses").filter(is_active=True)

        serializer = CoursePlanSerializer(plans, many=True)

        return Response(
            {
                "success": True,
                "count": plans.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class SubmissionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_slug):
        lesson = get_object_or_404(Lesson, slug=lesson_slug)
        submissions = Submission.objects.filter(
            user=request.user,
            task__lesson=lesson,
        ).order_by("-created_at")[:20]
        return Response(SubmissionResultSerializer(submissions, many=True).data)


_PROMO_CHARS = string.ascii_uppercase + string.digits
_PROMO_MAX_NUMBER = 500


def _generate_unique_code(length: int = 10) -> str:
    existing = set(PromoCode.objects.values_list("code", flat=True))
    for _ in range(100):
        code = "".join(secrets.choice(_PROMO_CHARS) for _ in range(length))
        if code not in existing:
            return code
    raise RuntimeError("Could not generate a unique promo code")


@extend_schema(tags=["Courses"], summary="Promo kodlar generatsiya (faqat admin)")
class GeneratePromoCodesView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        number = request.data.get("number")
        percent = request.data.get("percent")
        company_name = (request.data.get("company_name") or "").strip()

        if not isinstance(number, int) or not (1 <= number <= _PROMO_MAX_NUMBER):
            return Response(
                {"error": f"number 1 dan {_PROMO_MAX_NUMBER} gacha butun son bo'lishi kerak"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(percent, int) or not (1 <= percent <= 100):
            return Response(
                {"error": "percent 1 dan 100 gacha butun son bo'lishi kerak"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = None
        if company_name:
            company, _ = Company.objects.get_or_create(name=company_name)
        else:
            return Response(
                {"error": "company_name bosh"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes = []
        promo_objects = []
        for _ in range(number):
            code = _generate_unique_code()
            codes.append(code)
            promo_objects.append(
                PromoCode(
                    code=code,
                    max_uses=1,
                    discount_percent=percent,
                    is_active=True,
                    company=company,
                )
            )

        PromoCode.objects.bulk_create(promo_objects)

        # Build Excel file
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Promo Codes"

        header_fill = PatternFill("solid", fgColor="4472C4")
        header_font = Font(bold=True, color="FFFFFF")
        center = Alignment(horizontal="center")

        headers = ["#", "Korxona", "Promo Code", "Chegirma (%)", "Holat"]
        col_widths = [6, 25, 20, 16, 12]

        for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center
            ws.column_dimensions[cell.column_letter].width = width

        for row_idx, code in enumerate(codes, start=2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1).alignment = center
            ws.cell(row=row_idx, column=2, value=company_name or "—").alignment = center
            ws.cell(row=row_idx, column=3, value=code).alignment = center
            ws.cell(row=row_idx, column=4, value=percent).alignment = center
            ws.cell(row=row_idx, column=5, value="Aktiv").alignment = center

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        safe_company = company_name.replace(" ", "_") if company_name else "all"
        response["Content-Disposition"] = (
            f'attachment; filename="promocodes_{safe_company}_{percent}pct_{number}ta.xlsx"'
        )
        return response


def _promo_purchase_stats(purchases):
    """
    purchases: queryset of UserCoursePurchase with select_related("user", "course").
    Returns (detail_list, completed_count, halfway_count, just_started_count).
    Uses 2 extra queries regardless of how many purchases there are.
    """
    purchases = list(purchases)
    if not purchases:
        return [], 0, 0, 0

    user_ids = [p.user_id for p in purchases]
    course_ids = list({p.course_id for p in purchases})

    # Completed lesson counts per (user_id, course_id) — 1 query
    progress_rows = (
        LessonProgress.objects
        .filter(user_id__in=user_ids, lesson__module__course_id__in=course_ids, is_completed=True)
        .values("user_id", "lesson__module__course_id")
        .annotate(completed=Count("id"))
    )
    progress_map = {
        (r["user_id"], r["lesson__module__course_id"]): r["completed"]
        for r in progress_rows
    }

    # Total lessons per course — 1 query
    total_rows = (
        Course.objects
        .filter(id__in=course_ids)
        .annotate(total=Count("modules__lessons"))
        .values("id", "total")
    )
    total_map = {r["id"]: r["total"] for r in total_rows}

    detail = []
    for p in purchases:
        total = total_map.get(p.course_id, 0)
        completed_lessons = progress_map.get((p.user_id, p.course_id), 0)
        progress = round((completed_lessons / total) * 100, 2) if total > 0 else 0.0
        detail.append({
            "user_name": p.user.full_name,
            "user_telegram_id": p.user.telegram_id,
            "course": p.course.title,
            "progress": progress,
            "completed_lessons": completed_lessons,
            "total_lessons": total,
            "purchased_at": p.purchased_at,
        })

    completed_count = sum(1 for d in detail if d["progress"] >= 100)
    halfway_count = sum(1 for d in detail if 50 <= d["progress"] < 100)
    just_started_count = sum(1 for d in detail if d["progress"] < 50)

    return detail, completed_count, halfway_count, just_started_count


@extend_schema(tags=["Courses"], summary="Promo kod statistikasi — barcha (faqat admin)")
class PromoCodeStatsListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        promos = (
            PromoCode.objects
            .select_related("company")
            .annotate(total_purchases=Count("usercoursepurchase"))
            .order_by("-created_at")
        )
        data = []
        for promo in promos:
            purchases = (
                UserCoursePurchase.objects
                .filter(promo_code=promo)
                .select_related("user", "course")
            )
            _, completed, halfway, just_started = _promo_purchase_stats(purchases)
            data.append({
                "code": promo.code,
                "company": promo.company.name if promo.company else None,
                "discount_percent": promo.discount_percent,
                "is_active": promo.is_active,
                "total_purchases": promo.total_purchases,
                "completed_count": completed,
                "halfway_count": halfway,
                "just_started_count": just_started,
            })
        return Response({"count": len(data), "promo_codes": data})


@extend_schema(tags=["Courses"], summary="Bitta promo kod statistikasi (faqat admin)")
class PromoCodeStatsDetailView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, code):
        try:
            promo = PromoCode.objects.select_related("company").get(code=code)
        except PromoCode.DoesNotExist:
            return Response({"error": "Promo kod topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        purchases = (
            UserCoursePurchase.objects
            .filter(promo_code=promo)
            .select_related("user", "course")
            .order_by("-purchased_at")
        )
        detail, completed, halfway, just_started = _promo_purchase_stats(purchases)

        return Response({
            "code": promo.code,
            "company": promo.company.name if promo.company else None,
            "discount_percent": promo.discount_percent,
            "is_active": promo.is_active,
            "used_count": promo.used_count,
            "total_purchases": len(detail),
            "completed_count": completed,
            "halfway_count": halfway,
            "just_started_count": just_started,
            "purchases": detail,
        })

