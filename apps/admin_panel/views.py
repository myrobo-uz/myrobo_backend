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
from apps.core.models import Tag
from apps.core.pagination import StandardPagination
from apps.community.models import Topic, TopicComment
from apps.competitions.models import Competition, CompetitionParticipant, ParticipantStatus
from apps.gamification.models import Certificate, Rank, XPLog, XPReason
from apps.gamification.serializers import AwardXPRequestSerializer
from apps.gamification.utils import award_xp
from apps.projects.models import Project
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
    AdminCertificateSerializer,
    AdminCommentSerializer,
    AdminCompanySerializer,
    AdminCompetitionParticipantSerializer,
    AdminCompetitionSerializer,
    AdminTopicSerializer,
    AdminTopicCommentSerializer,
    AdminCoursePlanSerializer,
    AdminCourseSerializer,
    AdminCourseTypeSerializer,
    AdminDashboardSerializer,
    AdminLessonSerializer,
    AdminLessonTaskSerializer,
    AdminLessonTestSerializer,
    AdminModuleSerializer,
    AdminPromoCodeSerializer,
    AdminProjectSerializer,
    AdminPurchaseSerializer,
    AdminRankSerializer,
    AdminSubscriptionSerializer,
    AdminTaskTestCaseSerializer,
    AdminTeacherSerializer,
    AdminTagSerializer,
    AdminTestOptionSerializer,
    AdminTestQuestionSerializer,
    AdminTestResultSerializer,
    AdminTransactionSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminXPLogSerializer,
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


# ── Gamification: Ranks ─────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Gamification"])
class AdminRankViewSet(AdminReadWriteViewSet):
    serializer_class = AdminRankSerializer
    queryset = Rank.objects.all()


# ── Gamification: XP Logs (readonly) ─────────────────────────────────────────────

@extend_schema(tags=["Admin: Gamification"])
class AdminXPLogViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminXPLogSerializer

    def get_queryset(self):
        qs = XPLog.objects.select_related("user").order_by("-created_at")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        reason = self.request.query_params.get("reason")
        if reason:
            qs = qs.filter(reason=reason)
        return qs


# ── Gamification: Certificates (readonly) ────────────────────────────────────────

@extend_schema(tags=["Admin: Gamification"])
class AdminCertificateViewSet(AdminReadOnlyViewSet):
    serializer_class = AdminCertificateSerializer

    def get_queryset(self):
        qs = Certificate.objects.select_related("user", "course").order_by("-created_at")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


# ── Projects (moderation only — egasi foydalanuvchi, admin yaratmaydi) ─────────

@extend_schema(tags=["Admin: Projects"])
class AdminProjectViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = AdminProjectSerializer

    def get_queryset(self):
        qs = Project.objects.select_related("user").prefetch_related("tags").order_by("-created_at")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @extend_schema(summary="Loyihani arxivga olish", request=None)
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        from apps.projects.models import ProjectStatus
        project = self.get_object()
        project.status = ProjectStatus.ARCHIVED
        project.save(update_fields=["status", "updated_at"])
        return Response(AdminProjectSerializer(project).data)


# ── Competitions ───────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Competitions"])
class AdminCompetitionViewSet(AdminReadWriteViewSet):
    serializer_class = AdminCompetitionSerializer

    def get_queryset(self):
        return Competition.objects.prefetch_related("directions").annotate(
            participants_count=Count("participants", distinct=True)
        ).order_by("-start_date")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema(tags=["Admin: Competitions"])
class AdminCompetitionParticipantViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    serializer_class = AdminCompetitionParticipantSerializer

    def get_queryset(self):
        qs = CompetitionParticipant.objects.select_related("user", "competition").order_by("-created_at")
        competition_id = self.request.query_params.get("competition_id")
        if competition_id:
            qs = qs.filter(competition_id=competition_id)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @extend_schema(summary="Ishtirokchini g'olib deb belgilash va XP berish", request=None)
    @action(detail=True, methods=["post"], url_path="mark-winner")
    def mark_winner(self, request, pk=None):
        participant = self.get_object()
        participant.status = ParticipantStatus.WINNER
        if not participant.xp_awarded and participant.competition.xp_reward > 0:
            award_xp(
                participant.user, amount=participant.competition.xp_reward,
                reason=XPReason.COMPETITION_WIN,
                description=participant.competition.title, target=participant.competition,
            )
            participant.xp_awarded = True
        participant.save(update_fields=["status", "xp_awarded", "updated_at"])
        return Response(AdminCompetitionParticipantSerializer(participant).data)


# ── Community ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Community"])
class AdminTopicViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = AdminTopicSerializer

    def get_queryset(self):
        qs = Topic.objects.select_related("user").prefetch_related("tags").annotate(
            comments_count=Count("comments", distinct=True)
        ).order_by("-created_at")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        is_solved = self.request.query_params.get("is_solved")
        if is_solved is not None:
            qs = qs.filter(is_solved=is_solved.lower() == "true")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @extend_schema(summary="Mavzuni faollashtirish", request=None)
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        topic = self.get_object()
        topic.is_active = True
        topic.save(update_fields=["is_active", "updated_at"])
        return Response(AdminTopicSerializer(topic).data)

    @extend_schema(summary="Mavzuni yashirish", request=None)
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        topic = self.get_object()
        topic.is_active = False
        topic.save(update_fields=["is_active", "updated_at"])
        return Response(AdminTopicSerializer(topic).data)


@extend_schema(tags=["Admin: Community"])
class AdminTopicCommentViewSet(
    AdminBaseViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = AdminTopicCommentSerializer

    def get_queryset(self):
        qs = TopicComment.objects.select_related("user", "topic").order_by("-created_at")
        topic_id = self.request.query_params.get("topic_id")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    @extend_schema(summary="Izohni tasdiqlash", request=None)
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.is_active = True
        comment.save(update_fields=["is_active", "updated_at"])
        return Response(AdminTopicCommentSerializer(comment).data)

    @extend_schema(summary="Izohni rad etish", request=None)
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.is_active = False
        comment.save(update_fields=["is_active", "updated_at"])
        return Response(AdminTopicCommentSerializer(comment).data)


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

    @extend_schema(
        summary="Foydalanuvchiga qo'lda XP berish",
        request=AwardXPRequestSerializer,
        responses={200: AdminUserSerializer},
    )
    @action(detail=True, methods=["post"], url_path="award-xp")
    def award_xp_action(self, request, pk=None):
        user = self.get_object()
        serializer = AwardXPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        award_xp(
            user,
            amount=serializer.validated_data["amount"],
            reason=XPReason.MANUAL,
            description=serializer.validated_data.get("description", ""),
        )
        user.refresh_from_db()
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
        qs = Course.objects.select_related("course_type").prefetch_related("tags").order_by("-created_at")
        course_type = self.request.query_params.get("course_type")
        if course_type:
            qs = qs.filter(course_type_id=course_type)
        is_archived = self.request.query_params.get("is_archived")
        if is_archived is not None:
            qs = qs.filter(is_archived=is_archived.lower() == "true")
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @extend_schema(summary="Kursni arxivga olish", request=None)
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        course = self.get_object()
        course.is_archived = True
        course.save(update_fields=["is_archived", "updated_at"])
        return Response(AdminCourseSerializer(course).data)

    @extend_schema(summary="Kursni arxivdan chiqarish", request=None)
    @action(detail=True, methods=["post"], url_path="unarchive")
    def unarchive(self, request, pk=None):
        course = self.get_object()
        course.is_archived = False
        course.save(update_fields=["is_archived", "updated_at"])
        return Response(AdminCourseSerializer(course).data)


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
        qs = Articles.objects.select_related("type").prefetch_related("tags").order_by("-created_at")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        article_type = self.request.query_params.get("type_id")
        if article_type:
            qs = qs.filter(type_id=article_type)
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
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


# ── Tags ───────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Admin: Tags"])
class AdminTagViewSet(AdminReadWriteViewSet):
    serializer_class = AdminTagSerializer

    def get_queryset(self):
        qs = Tag.objects.annotate(
            courses_count=Count("courses", distinct=True),
            articles_count=Count("articles", distinct=True),
        ).order_by("name")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


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
