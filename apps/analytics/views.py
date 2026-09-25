from collections import defaultdict

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.courses.models import Course, CourseSubscription, LessonProgress, UserCoursePurchase, UserSubscription
from apps.courses.permission import IsAdminUser
from apps.payment.models import PaymeTransaction
from apps.users.authentication import CustomJWTAuthentication
from apps.users.models import User

from .models import ActivityType, LoginLog, UserActivity
from .presence import get_online_count, get_online_user_ids
from .serializers import (
    CourseProgressOverviewSerializer,
    CourseStudentProgressSerializer,
    DonationSerializer,
    OnlineUserSerializer,
    PeriodCountSerializer,
    PeriodDonationSerializer,
    UserActivitySerializer,
    UserActivitySummarySerializer,
)
from .utils import apply_period_trunc, course_progress_for_users

PERIOD_PARAM = OpenApiParameter(
    "period", str, description="daily | monthly | yearly (default: daily)", required=False
)
DATE_FROM_PARAM = OpenApiParameter("date_from", str, description="YYYY-MM-DD", required=False)
DATE_TO_PARAM = OpenApiParameter("date_to", str, description="YYYY-MM-DD", required=False)


class AnalyticsBaseView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]


def _apply_date_range(qs, request, field="created_at"):
    date_from = parse_date(request.query_params.get("date_from", "") or "")
    date_to = parse_date(request.query_params.get("date_to", "") or "")
    if date_from:
        qs = qs.filter(**{f"{field}__date__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{field}__date__lte": date_to})
    return qs


def _get_period(request) -> str:
    period = request.query_params.get("period", "daily")
    return period if period in ("daily", "monthly", "yearly") else "daily"


@extend_schema(tags=["Admin: Analytics"], summary="Umumiy statistika (dashboard snapshot)")
class AnalyticsOverviewView(AnalyticsBaseView):
    def get(self, request):
        today = timezone.now().date()

        total_users = User.objects.count()
        new_users_today = User.objects.filter(created_at__date=today).count()
        logins_today = LoginLog.objects.filter(created_at__date=today).count()

        donate_qs = PaymeTransaction.objects.filter(
            purpose=PaymeTransaction.PURPOSE_DONATE, state=PaymeTransaction.STATE_DONE
        )
        donations_total = donate_qs.aggregate(total=Sum("amount_tiyin"), count=Count("id"))
        donations_today = donate_qs.filter(created_at__date=today).aggregate(
            total=Sum("amount_tiyin"), count=Count("id")
        )

        return Response({
            "total_users": total_users,
            "new_users_today": new_users_today,
            "logins_today": logins_today,
            "online_now": get_online_count(),
            "total_courses": Course.objects.count(),
            "total_purchases": UserCoursePurchase.objects.count(),
            "donations_today": {
                "count": donations_today["count"] or 0,
                "total_som": (donations_today["total"] or 0) / 100,
            },
            "donations_total": {
                "count": donations_total["count"] or 0,
                "total_som": (donations_total["total"] or 0) / 100,
            },
        })


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Kunlik/oylik/yillik ro'yxatdan o'tishlar",
    parameters=[PERIOD_PARAM, DATE_FROM_PARAM, DATE_TO_PARAM],
    responses={200: PeriodCountSerializer(many=True)},
)
class RegistrationsStatsView(AnalyticsBaseView):
    def get(self, request):
        period = _get_period(request)
        qs = _apply_date_range(User.objects.all(), request)
        grouped = apply_period_trunc(qs, period, "created_at").annotate(count=Count("id"))
        data = [{"period": row["period"], "count": row["count"]} for row in grouped]
        return Response(data)


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Kunlik/oylik/yillik login statistikasi",
    parameters=[PERIOD_PARAM, DATE_FROM_PARAM, DATE_TO_PARAM],
    responses={200: PeriodCountSerializer(many=True)},
)
class LoginsStatsView(AnalyticsBaseView):
    def get(self, request):
        period = _get_period(request)
        qs = _apply_date_range(LoginLog.objects.all(), request)
        grouped = apply_period_trunc(qs, period, "created_at").annotate(count=Count("id"))
        data = [{"period": row["period"], "count": row["count"]} for row in grouped]
        return Response(data)


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Kunlik/oylik/yillik donate statistikasi",
    parameters=[PERIOD_PARAM, DATE_FROM_PARAM, DATE_TO_PARAM],
    responses={200: PeriodDonationSerializer(many=True)},
)
class DonationsStatsView(AnalyticsBaseView):
    def get(self, request):
        period = _get_period(request)
        qs = _apply_date_range(
            PaymeTransaction.objects.filter(
                purpose=PaymeTransaction.PURPOSE_DONATE, state=PaymeTransaction.STATE_DONE
            ),
            request,
        )
        grouped = apply_period_trunc(qs, period, "created_at").annotate(
            count=Count("id"), total_tiyin=Sum("amount_tiyin")
        )
        data = [
            {
                "period": row["period"],
                "count": row["count"],
                "total_som": (row["total_tiyin"] or 0) / 100,
            }
            for row in grouped
        ]
        return Response(data)


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Kim qancha donate qildi (ro'yxat)",
    parameters=[
        OpenApiParameter("user_id", str, required=False),
        DATE_FROM_PARAM,
        DATE_TO_PARAM,
    ],
)
class DonationsListView(generics.ListAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = DonationSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            PaymeTransaction.objects
            .select_related("user")
            .filter(purpose=PaymeTransaction.PURPOSE_DONATE, state=PaymeTransaction.STATE_DONE)
            .order_by("-created_at")
        )
        qs = _apply_date_range(qs, self.request)
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs


@extend_schema(tags=["Admin: Analytics"], summary="Har bir kurs bo'yicha umumiy progress")
class CourseProgressOverviewView(AnalyticsBaseView):
    def get(self, request):
        now = timezone.now()
        courses = list(Course.objects.annotate(total_lessons=Count("modules__lessons")))
        course_ids = [c.id for c in courses]

        enrolled_by_course = defaultdict(set)

        for row in UserCoursePurchase.objects.filter(course_id__in=course_ids).values("course_id", "user_id"):
            enrolled_by_course[row["course_id"]].add(row["user_id"])

        for row in UserSubscription.objects.filter(
            is_active=True, expires_at__gt=now, plan__courses__id__in=course_ids
        ).values("user_id", "plan__courses__id"):
            cid = row["plan__courses__id"]
            if cid:
                enrolled_by_course[cid].add(row["user_id"])

        for row in CourseSubscription.objects.filter(
            course_id__in=course_ids, is_active=True, expires_at__gt=now
        ).values("course_id", "user_id"):
            enrolled_by_course[row["course_id"]].add(row["user_id"])

        all_user_ids = list({uid for uids in enrolled_by_course.values() for uid in uids})
        progress_rows = (
            LessonProgress.objects
            .filter(user_id__in=all_user_ids, lesson__module__course_id__in=course_ids, is_completed=True)
            .values("user_id", "lesson__module__course_id")
            .annotate(completed=Count("id"))
        )
        progress_map = {(r["user_id"], r["lesson__module__course_id"]): r["completed"] for r in progress_rows}

        data = []
        for c in courses:
            uids = enrolled_by_course.get(c.id, set())
            enrolled_count = len(uids)
            if enrolled_count and c.total_lessons:
                percents = [
                    round((progress_map.get((uid, c.id), 0) / c.total_lessons) * 100, 2) for uid in uids
                ]
                avg_percent = round(sum(percents) / len(percents), 2)
            else:
                avg_percent = 0.0
            data.append({
                "course_id": c.id,
                "course_title": c.title,
                "enrolled_count": enrolled_count,
                "total_lessons": c.total_lessons,
                "avg_completion_percent": avg_percent,
            })

        serializer = CourseProgressOverviewSerializer(data, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Admin: Analytics"], summary="Kursdagi har bir student progressi")
class CourseProgressDetailView(AnalyticsBaseView):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        now = timezone.now()

        user_ids = set(
            UserCoursePurchase.objects.filter(course=course).values_list("user_id", flat=True)
        )
        user_ids |= set(
            UserSubscription.objects.filter(
                is_active=True, expires_at__gt=now, plan__courses=course
            ).values_list("user_id", flat=True)
        )
        user_ids |= set(
            CourseSubscription.objects.filter(
                course=course, is_active=True, expires_at__gt=now
            ).values_list("user_id", flat=True)
        )
        user_ids = list(user_ids)

        progress_map = course_progress_for_users(course, user_ids)
        users_map = {u.id: u for u in User.objects.filter(id__in=user_ids)}

        data = []
        for user_id in user_ids:
            user = users_map.get(user_id)
            if not user:
                continue
            progress = progress_map.get(user_id, {"completed_lessons": 0, "total_lessons": 0, "percent": 0.0})
            data.append({
                "user_id": user_id,
                "full_name": user.full_name,
                "phone_number": user.phone_number,
                **progress,
            })

        data.sort(key=lambda d: d["percent"], reverse=True)
        serializer = CourseStudentProgressSerializer(data, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Admin: Analytics"], summary="Hozir onlayn foydalanuvchilar")
class OnlineUsersView(AnalyticsBaseView):
    def get(self, request):
        online_ids = get_online_user_ids()
        users = list(User.objects.filter(id__in=online_ids).values("id", "full_name", "phone_number"))
        serializer = OnlineUserSerializer(users, many=True)
        return Response({"count": len(online_ids), "users": serializer.data})


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Foydalanuvchilar faoliyati jurnali (action log)",
    parameters=[
        OpenApiParameter("user_id", str, required=False, description="Faqat shu foydalanuvchi"),
        OpenApiParameter(
            "action", str, required=False,
            description="login | course_view | lesson_view | lesson_complete | "
                        "course_purchase | task_submit | test_submit | article_view | profile_update",
        ),
        DATE_FROM_PARAM,
        DATE_TO_PARAM,
    ],
    responses={200: UserActivitySerializer(many=True)},
)
class UserActivityListView(generics.ListAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = UserActivitySerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = UserActivity.objects.select_related("user").all()
        qs = _apply_date_range(qs, self.request)
        user_id = self.request.query_params.get("user_id")
        action = self.request.query_params.get("action")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if action:
            qs = qs.filter(action=action)
        return qs


@extend_schema(
    tags=["Admin: Analytics"],
    summary="Bitta foydalanuvchi faoliyati bo'yicha xulosa",
)
class UserActivitySummaryView(AnalyticsBaseView):
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        activities = UserActivity.objects.filter(user=user)

        action_counts = dict(
            activities.values("action").annotate(count=Count("id")).values_list("action", "count")
        )
        last_login = (
            activities.filter(action=ActivityType.LOGIN)
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        last_seen = activities.order_by("-created_at").values_list("created_at", flat=True).first()
        online_ids = get_online_user_ids()

        data = {
            "user_id": user.id,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "is_online": str(user.id) in online_ids,
            "login_count": action_counts.get(ActivityType.LOGIN, 0),
            "last_login": last_login,
            "last_seen": last_seen,
            "total_activities": sum(action_counts.values()),
            "action_counts": action_counts,
        }
        serializer = UserActivitySummarySerializer(data)
        return Response(serializer.data)
