from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.articles.models import ArticleType, Articles, Comment
from apps.core.pagination import StandardPagination
from apps.courses.models import (
    Company,
    CoursePlan,
    CourseType,
    Course,
    Module,
    Lesson,
    LessonTask,
    TaskTestCase,
    PromoCode,
    UserSubscription,
    UserCoursePurchase,
)
from apps.courses.permission import IsAdminUser
from apps.lessontest.models import LessonTest, TestQuestion, TestOption, TestResult
from apps.payment.models import PaymeTransaction
from apps.teachers.models import Teacher
from apps.users.authentication import CustomJWTAuthentication
from apps.users.models import User

from .serializers import (
    AdminAddBalanceSerializer,
    AdminArticleSerializer,
    AdminArticleTypeSerializer,
    AdminCommentSerializer,
    AdminCompanySerializer,
    AdminCoursePlanSerializer,
    AdminCourseSerializer,
    AdminCourseTypeSerializer,
    AdminDashboardSerializer,
    AdminLessonSerializer,
    AdminLessonTaskSerializer,
    AdminLessonTestSerializer,
    AdminModuleSerializer,
    AdminPromoCodeSerializer,
    AdminPurchaseSerializer,
    AdminSubscriptionSerializer,
    AdminTaskTestCaseSerializer,
    AdminTeacherSerializer,
    AdminTestOptionSerializer,
    AdminTestQuestionSerializer,
    AdminTestResultSerializer,
    AdminTransactionSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)


class AdminBaseViewSet(viewsets.GenericViewSet):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = StandardPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class AdminReadWriteViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass


class AdminReadOnlyViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    pass


# ── Dashboard ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Dashboard"], summary="Admin dashboard statistikasi")
class AdminDashboardView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()

        user_stats = User.objects.aggregate(
            total=Count("id"),
            blocked=Count("id", filter=Q(is_blocked=True)),
            admins=Count("id", filter=Q(is_admin=True)),
        )

        course_stats = {
            "total_courses": Course.objects.count(),
            "total_modules": Module.objects.count(),
            "total_lessons": Lesson.objects.count(),
            "total_teachers": Teacher.objects.count(),
            "active_subscriptions": UserSubscription.objects.filter(
                is_active=True, expires_at__gt=now
            ).count(),
            "total_purchases": UserCoursePurchase.objects.count(),
        }

        txn_agg = PaymeTransaction.objects.filter(state=PaymeTransaction.STATE_DONE).aggregate(
            total_tiyin=Sum("amount_tiyin"),
            count=Count("id"),
        )
        total_tiyin = txn_agg["total_tiyin"] or 0
        revenue_stats = {
            "completed_transactions": txn_agg["count"] or 0,
            "pending_transactions": PaymeTransaction.objects.filter(state=PaymeTransaction.STATE_PENDING).count(),
            "cancelled_transactions": PaymeTransaction.objects.filter(state=PaymeTransaction.STATE_CANCELED).count(),
            "total_revenue_tiyin": total_tiyin,
            "total_revenue_som": round(total_tiyin / 100, 2),
        }

        content_stats = {
            "total_articles": Articles.objects.count(),
            "active_articles": Articles.objects.filter(is_active=True).count(),
            "total_comments": Comment.objects.count(),
            "pending_comments": Comment.objects.filter(is_active=False).count(),
            "total_promo_codes": PromoCode.objects.count(),
            "active_promo_codes": PromoCode.objects.filter(is_active=True).count(),
        }

        return Response({
            "users": user_stats,
            "courses": course_stats,
            "revenue": revenue_stats,
            "content": content_stats,
        })


# ── Users ──────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Users"])
class AdminUserViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        params = self.request.query_params

        search = params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(phone_number__icontains=search)
                | Q(telegram_username__icontains=search)
            )

        is_blocked = params.get("is_blocked")
        if is_blocked is not None:
            qs = qs.filter(is_blocked=is_blocked.lower() == "true")

        is_admin = params.get("is_admin")
        if is_admin is not None:
            qs = qs.filter(is_admin=is_admin.lower() == "true")

        return qs

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    @extend_schema(
        summary="Foydalanuvchini bloklash / blokdan chiqarish",
        request=None,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"], url_path="toggle-block")
    def toggle_block(self, request, pk=None):
        user = self.get_object()
        user.is_blocked = not user.is_blocked
        user.save(update_fields=["is_blocked", "updated_at"])
        return Response(AdminUserSerializer(user).data)

    @extend_schema(
        summary="Foydalanuvchi balansini to'ldirish",
        request=AdminAddBalanceSerializer,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"], url_path="add-balance")
    def add_balance(self, request, pk=None):
        user = self.get_object()
        serializer = AdminAddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        user.balance = (user.balance or Decimal("0")) + amount
        user.save(update_fields=["balance", "updated_at"])
        return Response(AdminUserSerializer(user).data)


# ── Course Types ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminCourseTypeViewSet(AdminReadWriteViewSet):
    serializer_class = AdminCourseTypeSerializer

    def get_queryset(self):
        return CourseType.objects.annotate(courses_count=Count("courses")).order_by("-created_at")


# ── Courses ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminCourseViewSet(AdminReadWriteViewSet):
    serializer_class = AdminCourseSerializer

    def get_queryset(self):
        qs = Course.objects.select_related("course_type").order_by("-created_at")
        course_type = self.request.query_params.get("course_type")
        if course_type:
            qs = qs.filter(course_type_id=course_type)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs


# ── Modules ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminModuleViewSet(AdminReadWriteViewSet):
    serializer_class = AdminModuleSerializer

    def get_queryset(self):
        qs = Module.objects.select_related("course").annotate(
            lessons_count=Count("lessons")
        ).order_by("course", "order", "id")
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


# ── Lessons ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminLessonViewSet(AdminReadWriteViewSet):
    serializer_class = AdminLessonSerializer

    def get_queryset(self):
        qs = Lesson.objects.select_related("module__course").order_by("module", "order", "id")
        module_id = self.request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(module__course_id=course_id)
        lesson_type = self.request.query_params.get("lesson_type")
        if lesson_type:
            qs = qs.filter(lesson_type=lesson_type)
        return qs


# ── Lesson Tasks ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminLessonTaskViewSet(AdminReadWriteViewSet):
    serializer_class = AdminLessonTaskSerializer

    def get_queryset(self):
        qs = LessonTask.objects.select_related("lesson__module__course").order_by("-created_at")
        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs


# ── Task Test Cases ────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminTaskTestCaseViewSet(AdminReadWriteViewSet):
    serializer_class = AdminTaskTestCaseSerializer

    def get_queryset(self):
        qs = TaskTestCase.objects.select_related("task").order_by("-created_at")
        task_id = self.request.query_params.get("task_id")
        if task_id:
            qs = qs.filter(task_id=task_id)
        is_hidden = self.request.query_params.get("is_hidden")
        if is_hidden is not None:
            qs = qs.filter(is_hidden=is_hidden.lower() == "true")
        return qs


# ── Teachers ───────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Teachers"])
class AdminTeacherViewSet(AdminReadWriteViewSet):
    serializer_class = AdminTeacherSerializer

    def get_queryset(self):
        qs = Teacher.objects.annotate(
            courses_count=Count("courses")
        ).prefetch_related("courses").order_by("first_name", "last_name")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(username__icontains=search)
            )
        return qs


# ── Article Types ──────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Articles"])
class AdminArticleTypeViewSet(AdminReadWriteViewSet):
    serializer_class = AdminArticleTypeSerializer

    def get_queryset(self):
        return ArticleType.objects.annotate(
            articles_count=Count("articles")
        ).order_by("-created_at")


# ── Articles ───────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Articles"])
class AdminArticleViewSet(AdminReadWriteViewSet):
    serializer_class = AdminArticleSerializer

    def get_queryset(self):
        qs = Articles.objects.select_related("type").order_by("-created_at")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        article_type = self.request.query_params.get("type_id")
        if article_type:
            qs = qs.filter(type_id=article_type)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @extend_schema(summary="Maqolani faollashtirish", request=None)
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        article = self.get_object()
        article.is_active = True
        article.save(update_fields=["is_active", "updated_at"])
        return Response(AdminArticleSerializer(article).data)

    @extend_schema(summary="Maqolani o'chirish (faolsizlashtirish)", request=None)
    @action(detail=True, methods=["post"], url_path="unpublish")
    def unpublish(self, request, pk=None):
        article = self.get_object()
        article.is_active = False
        article.save(update_fields=["is_active", "updated_at"])
        return Response(AdminArticleSerializer(article).data)


# ── Comments ───────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Articles"])
class AdminCommentViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = AdminCommentSerializer

    def get_queryset(self):
        qs = Comment.objects.select_related("user", "article").order_by("-created_at")
        article_id = self.request.query_params.get("article_id")
        if article_id:
            qs = qs.filter(article_id=article_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    @extend_schema(summary="Kommentariyani tasdiqlash", request=None)
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.is_active = True
        comment.save(update_fields=["is_active", "updated_at"])
        return Response(AdminCommentSerializer(comment).data)

    @extend_schema(summary="Kommentariyani rad etish", request=None)
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.is_active = False
        comment.save(update_fields=["is_active", "updated_at"])
        return Response(AdminCommentSerializer(comment).data)


# ── Companies ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Promo"])
class AdminCompanyViewSet(AdminReadWriteViewSet):
    serializer_class = AdminCompanySerializer

    def get_queryset(self):
        return Company.objects.annotate(
            promo_codes_count=Count("promocodes")
        ).order_by("-created_at")


# ── Promo Codes ────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Promo"])
class AdminPromoCodeViewSet(AdminReadWriteViewSet):
    serializer_class = AdminPromoCodeSerializer

    def get_queryset(self):
        qs = PromoCode.objects.select_related("company").order_by("-created_at")
        company_id = self.request.query_params.get("company_id")
        if company_id:
            qs = qs.filter(company_id=company_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(company__name__icontains=search))
        return qs


# ── Course Plans ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Courses"])
class AdminCoursePlanViewSet(AdminReadWriteViewSet):
    serializer_class = AdminCoursePlanSerializer

    def get_queryset(self):
        return CoursePlan.objects.prefetch_related("courses").annotate(
            subscribers_count=Count("user_subscriptions", filter=Q(user_subscriptions__is_active=True))
        ).order_by("-created_at")


# ── Subscriptions ──────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Sales"])
class AdminSubscriptionViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminSubscriptionSerializer

    def get_queryset(self):
        qs = UserSubscription.objects.select_related("user", "plan", "promo_code").order_by("-subscribed_at")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        plan_id = self.request.query_params.get("plan_id")
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search)
                | Q(user__phone_number__icontains=search)
            )
        return qs


# ── Purchases ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Sales"])
class AdminPurchaseViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminPurchaseSerializer

    def get_queryset(self):
        qs = UserCoursePurchase.objects.select_related("user", "course", "promo_code").order_by("-purchased_at")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search)
                | Q(course__title__icontains=search)
            )
        return qs


# ── Transactions ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Sales"])
class AdminTransactionViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminTransactionSerializer

    def get_queryset(self):
        qs = PaymeTransaction.objects.select_related("user").order_by("-created_at")
        state = self.request.query_params.get("state")
        if state is not None:
            qs = qs.filter(state=state)
        purpose = self.request.query_params.get("purpose")
        if purpose is not None:
            qs = qs.filter(purpose=purpose)
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search)
                | Q(payme_transaction_id__icontains=search)
            )
        return qs


# ── Lesson Tests ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: LessonTests"])
class AdminLessonTestViewSet(AdminReadWriteViewSet):
    serializer_class = AdminLessonTestSerializer

    def get_queryset(self):
        qs = LessonTest.objects.select_related("lesson__module__course").annotate(
            questions_count=Count("questions")
        ).order_by("-created_at")
        lesson_id = self.request.query_params.get("lesson_id")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(lesson__module__course_id=course_id)
        return qs


# ── Test Questions ─────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: LessonTests"])
class AdminTestQuestionViewSet(AdminReadWriteViewSet):
    serializer_class = AdminTestQuestionSerializer

    def get_queryset(self):
        qs = TestQuestion.objects.select_related("test").prefetch_related("options").annotate(
            options_count=Count("options")
        ).order_by("test", "order", "id")
        test_id = self.request.query_params.get("test_id")
        if test_id:
            qs = qs.filter(test_id=test_id)
        return qs


# ── Test Options ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: LessonTests"])
class AdminTestOptionViewSet(AdminReadWriteViewSet):
    serializer_class = AdminTestOptionSerializer

    def get_queryset(self):
        qs = TestOption.objects.select_related("question").order_by("question", "order", "id")
        question_id = self.request.query_params.get("question_id")
        if question_id:
            qs = qs.filter(question_id=question_id)
        is_correct = self.request.query_params.get("is_correct")
        if is_correct is not None:
            qs = qs.filter(is_correct=is_correct.lower() == "true")
        return qs


# ── Test Results ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: LessonTests"])
class AdminTestResultViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminTestResultSerializer

    def get_queryset(self):
        qs = TestResult.objects.select_related("user", "test__lesson").order_by("-created_at")
        test_id = self.request.query_params.get("test_id")
        if test_id:
            qs = qs.filter(test_id=test_id)
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        is_passed = self.request.query_params.get("is_passed")
        if is_passed is not None:
            qs = qs.filter(is_passed=is_passed.lower() == "true")
        return qs
