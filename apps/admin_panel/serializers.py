from rest_framework import serializers

from apps.articles.models import ArticleType, Articles, Comment
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
            "full_name", "avatar", "balance", "is_blocked", "is_admin",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "telegram_id", "created_at", "updated_at"]


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
            "price", "image", "slug", "views", "created_at", "updated_at",
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
            "image", "views", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "created_at", "updated_at"]


# ── Comments ───────────────────────────────────────────────────────────────────

class AdminCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    article_slug = serializers.CharField(source="article.slug", read_only=True)
    article_title = serializers.CharField(source="article.title", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id", "article", "article_slug", "article_title",
            "user", "user_name", "text", "is_active", "created_at",
        ]
        read_only_fields = ["id", "user", "article_slug", "article_title", "user_name", "created_at"]


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
    plan_title = serializers.CharField(source="plan.title", read_only=True)
    promo_code_str = serializers.CharField(source="promo_code.code", read_only=True, allow_null=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id", "user", "user_name", "user_telegram_id",
            "plan", "plan_title", "promo_code", "promo_code_str",
            "original_price", "final_price",
            "subscribed_at", "expires_at", "is_active", "is_valid",
        ]
        read_only_fields = ["id", "subscribed_at"]


# ── Purchases ──────────────────────────────────────────────────────────────────

class AdminPurchaseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    promo_code_str = serializers.CharField(source="promo_code.code", read_only=True, allow_null=True)

    class Meta:
        model = UserCoursePurchase
        fields = [
            "id", "user", "user_name", "user_telegram_id",
            "course", "course_title", "promo_code", "promo_code_str",
            "original_price", "final_price", "purchased_at",
        ]
        read_only_fields = ["id", "purchased_at"]


# ── Payment Transactions ───────────────────────────────────────────────────────

class AdminTransactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_telegram_id = serializers.IntegerField(source="user.telegram_id", read_only=True)
    amount_som = serializers.SerializerMethodField()
    state_display = serializers.CharField(source="get_state_display", read_only=True)
    purpose_display = serializers.CharField(source="get_purpose_display", read_only=True)

    class Meta:
        model = PaymeTransaction
        fields = [
            "id", "provider", "purpose", "purpose_display", "user", "user_name", "user_telegram_id",
            "payme_transaction_id", "amount_tiyin", "amount_som",
            "state", "state_display",
            "create_time", "perform_time", "cancel_time",
            "reason", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_amount_som(self, obj):
        return obj.amount_som()


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
    test_title = serializers.CharField(source="test.title", read_only=True)
    lesson_title = serializers.CharField(source="test.lesson.title", read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id", "user", "user_name", "user_telegram_id",
            "test", "test_title", "lesson_title",
            "total_questions", "correct_count", "incorrect_count",
            "unanswered_count", "score_percent", "is_passed", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ── Dashboard ──────────────────────────────────────────────────────────────────

class AdminDashboardSerializer(serializers.Serializer):
    users = serializers.DictField()
    courses = serializers.DictField()
    revenue = serializers.DictField()
    content = serializers.DictField()
