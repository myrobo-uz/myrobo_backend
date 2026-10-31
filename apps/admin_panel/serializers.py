from rest_framework import serializers

from apps.articles.models import ArticleType, Articles, Comment
from apps.core.models import Tag
from apps.core.utils import get_avatar_url
from apps.community.models import Topic, TopicComment
from apps.competitions.models import Competition, CompetitionParticipant
from apps.gamification.models import Certificate, Rank, XPLog
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
from apps.lessontest.models import LessonTest, TestQuestion, TestOption, TestResult, TestAnswer
from apps.payment.models import PaymeTransaction
from apps.teachers.models import Teacher
from apps.users.models import User


# ── Users ─────────────────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "telegram_id", "phone_number", "telegram_username",
            "full_name", "avatar", "balance", "is_blocked", "is_admin", "xp",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "telegram_id", "xp", "created_at", "updated_at"]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone_number", "balance", "is_blocked", "is_admin", "avatar"]


class AdminAddBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)


# ── Course Types ───────────────────────────────────────────────────────────────

class AdminCourseTypeSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CourseType
        fields = ["id", "title", "slug", "courses_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


# ── Courses ────────────────────────────────────────────────────────────────────

class AdminCourseSerializer(serializers.ModelSerializer):
    course_type_title = serializers.CharField(source="course_type.title", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "course_type", "course_type_title", "title", "description",
            "price", "image", "slug", "views", "tags", "is_archived", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "created_at", "updated_at"]


# ── Modules ────────────────────────────────────────────────────────────────────

class AdminModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(read_only=True, default=0)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Module
        fields = ["id", "course", "course_title", "title", "slug", "order", "lessons_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


# ── Lessons ────────────────────────────────────────────────────────────────────

class AdminLessonSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id", "module", "module_title", "lesson_type", "title",
            "description", "video_url", "slug", "order", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


# ── Lesson Tasks ───────────────────────────────────────────────────────────────

class AdminLessonTaskSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonTask
        fields = [
            "id", "lesson", "lesson_title", "title", "description",
            "statement", "sample_input", "sample_output", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── Task Test Cases ────────────────────────────────────────────────────────────

class AdminTaskTestCaseSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TaskTestCase
        fields = ["id", "task", "task_title", "input_data", "expected_output", "is_hidden", "created_at"]
        read_only_fields = ["id", "created_at"]


# ── Teachers ───────────────────────────────────────────────────────────────────

class AdminTeacherSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Teacher
        fields = [
            "id", "first_name", "last_name", "middle_name", "username",
            "slug", "job", "about", "direction", "experience", "work_place",
            "image", "courses", "courses_count", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


# ── Article Types ──────────────────────────────────────────────────────────────

class AdminArticleTypeSerializer(serializers.ModelSerializer):
    articles_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = ArticleType
        fields = ["id", "title", "slug", "articles_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


# ── Articles ───────────────────────────────────────────────────────────────────

class AdminArticleSerializer(serializers.ModelSerializer):
    type_title = serializers.CharField(source="type.title", read_only=True)

    class Meta:
        model = Articles
        fields = [
            "id", "type", "type_title", "title", "slug", "description",
            "image", "views", "tags", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "created_at", "updated_at"]


# ── Comments ───────────────────────────────────────────────────────────────────

class AdminCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    article_slug = serializers.CharField(source="article.slug", read_only=True)
    article_title = serializers.CharField(source="article.title", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id", "article", "article_slug", "article_title",
            "user", "user_name", "user_avatar", "text", "is_active", "created_at",
        ]
        read_only_fields = ["id", "user", "article_slug", "article_title", "user_name", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Companies ──────────────────────────────────────────────────────────────────

class AdminCompanySerializer(serializers.ModelSerializer):
    promo_codes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Company
        fields = ["id", "name", "description", "promo_codes_count", "created_at"]
        read_only_fields = ["id", "created_at"]


# ── Promo Codes ────────────────────────────────────────────────────────────────

class AdminPromoCodeSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            "id", "company", "company_name", "code", "discount_percent",
            "is_active", "max_uses", "used_count", "valid_from", "valid_to",
            "is_valid", "created_at",
        ]
        read_only_fields = ["id", "used_count", "created_at"]

    def get_is_valid(self, obj):
        return obj.is_valid()


# ── Course Plans ───────────────────────────────────────────────────────────────

class AdminCoursePlanSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CoursePlan
        fields = [
            "id", "title", "description", "courses", "duration_days",
            "price", "is_active", "subscribers_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── Subscriptions ──────────────────────────────────────────────────────────────

class AdminSubscriptionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    plan_title = serializers.CharField(source="plan.title", read_only=True)
    promo_code_str = serializers.CharField(source="promo_code.code", read_only=True, allow_null=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id", "user", "user_name", "user_telegram_id", "user_avatar",
            "plan", "plan_title", "promo_code", "promo_code_str",
            "original_price", "final_price",
            "subscribed_at", "expires_at", "is_active", "is_valid",
        ]
        read_only_fields = ["id", "subscribed_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Purchases ──────────────────────────────────────────────────────────────────

class AdminPurchaseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)
    promo_code_str = serializers.CharField(source="promo_code.code", read_only=True, allow_null=True)

    class Meta:
        model = UserCoursePurchase
        fields = [
            "id", "user", "user_name", "user_telegram_id", "user_avatar",
            "course", "course_title", "promo_code", "promo_code_str",
            "original_price", "final_price", "purchased_at",
        ]
        read_only_fields = ["id", "purchased_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Payment Transactions ───────────────────────────────────────────────────────

class AdminTransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    amount_som = serializers.SerializerMethodField()
    state_display = serializers.CharField(source="get_state_display", read_only=True)
    purpose_display = serializers.CharField(source="get_purpose_display", read_only=True)

    class Meta:
        model = PaymeTransaction
        fields = [
            "id", "provider", "purpose", "purpose_display", "user", "user_name", "user_telegram_id",
            "user_avatar", "payme_transaction_id", "amount_tiyin", "amount_som",
            "state", "state_display",
            "create_time", "perform_time", "cancel_time",
            "reason", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_amount_som(self, obj):
        return obj.amount_som()

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Lesson Tests ───────────────────────────────────────────────────────────────

class AdminTestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOption
        fields = ["id", "question", "text", "image", "is_correct", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class AdminTestQuestionSerializer(serializers.ModelSerializer):
    options = AdminTestOptionSerializer(many=True, read_only=True)
    options_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = TestQuestion
        fields = ["id", "test", "text", "image", "order", "options_count", "options", "created_at"]
        read_only_fields = ["id", "created_at"]


class AdminLessonTestSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="lesson.slug", read_only=True)
    questions_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = LessonTest
        fields = [
            "id", "lesson", "lesson_title", "lesson_slug",
            "title", "description", "duration_minutes", "pass_score",
            "questions_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AdminTestResultSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    test_title = serializers.CharField(source="test.title", read_only=True)
    lesson_title = serializers.CharField(source="test.lesson.title", read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id", "user", "user_name", "user_telegram_id", "user_avatar",
            "test", "test_title", "lesson_title",
            "total_questions", "correct_count", "incorrect_count",
            "unanswered_count", "score_percent", "is_passed", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Tags ───────────────────────────────────────────────────────────────────────

class AdminTagSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True, default=0)
    articles_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "courses_count", "articles_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


# ── Gamification ───────────────────────────────────────────────────────────────

class AdminRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ["id", "title", "slug", "min_xp", "icon", "order", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class AdminXPLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = XPLog
        fields = [
            "id", "user", "user_name", "user_avatar", "amount", "reason", "reason_display",
            "description", "target_type", "target_id", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


class AdminCertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "user", "user_name", "user_avatar", "course", "course_title",
            "certificate_number", "created_at",
        ]
        read_only_fields = ["id", "certificate_number", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Projects ───────────────────────────────────────────────────────────────────

class AdminProjectSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "user", "user_name", "user_avatar", "title", "slug", "description", "image",
            "tags", "status", "simulator_ref", "board_type", "code", "components_json",
            "wires_json", "files", "is_public", "views", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "user_name", "slug", "views", "created_at", "updated_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Competitions ───────────────────────────────────────────────────────────────

class AdminCompetitionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    participants_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Competition
        fields = [
            "id", "title", "slug", "description", "requirements", "image",
            "directions", "start_date", "end_date", "xp_reward", "is_published",
            "author", "status", "participants_count", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class AdminCompetitionParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    competition_title = serializers.CharField(source="competition.title", read_only=True)

    class Meta:
        model = CompetitionParticipant
        fields = [
            "id", "competition", "competition_title", "user", "user_name", "user_avatar",
            "status", "submission_note", "xp_awarded", "created_at",
        ]
        read_only_fields = ["id", "competition", "user", "xp_awarded", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Community ──────────────────────────────────────────────────────────────────

class AdminTopicSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = [
            "id", "user", "user_name", "user_avatar", "title", "slug", "description", "tags",
            "is_solved", "is_active", "views", "comments_count", "created_at",
        ]
        read_only_fields = ["id", "user", "user_name", "slug", "views", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


class AdminTopicCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_avatar = serializers.SerializerMethodField()
    topic_title = serializers.CharField(source="topic.title", read_only=True)

    class Meta:
        model = TopicComment
        fields = [
            "id", "topic", "topic_title", "user", "user_name", "user_avatar",
            "text", "is_accepted", "is_active", "created_at",
        ]
        read_only_fields = ["id", "topic", "user", "created_at"]

    def get_user_avatar(self, obj):
        return get_avatar_url(obj.user, self.context.get("request"))


# ── Dashboard ──────────────────────────────────────────────────────────────────

class AdminDashboardSerializer(serializers.Serializer):
    users = serializers.DictField()
    courses = serializers.DictField()
    revenue = serializers.DictField()
    content = serializers.DictField()
