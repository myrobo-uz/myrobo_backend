from rest_framework import serializers

from .models import (
    Course,
    CoursePlan,
    CourseSubscription,
    CourseType,
    Lesson,
    LessonTask,
    Module,
    PromoCode,
    Submission,
    TaskTestCase,
    UserCoursePurchase,
    UserSubscription,
    LessonProgress
)


class PurchaseCourseRequestSerializer(serializers.Serializer):
    purchase_type = serializers.ChoiceField(choices=("course", "subscription"))
    plan_id = serializers.UUIDField(required=False, help_text="subscription uchun")
    promo_code = serializers.CharField(required=False, allow_blank=True)


class CompleteLessonResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    lesson = serializers.CharField()


class CourseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseType
        fields = ["id", "title", "slug", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class TaskTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTestCase
        fields = ["input_data", "expected_output"]


class LessonTaskSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()

    class Meta:
        model = LessonTask
        fields = [
            "id",
            "title",
            "description",
            "statement",
            "sample_input",
            "sample_output",
            "test_cases",
        ]

    def get_test_cases(self, obj):
        visible_test_cases = obj.test_cases.filter(is_hidden=False)
        return TaskTestCaseSerializer(visible_test_cases, many=True).data
class LessonDetailSerializer(serializers.ModelSerializer):
    tasks = LessonTaskSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "lesson_type",
            "video_url",
            "slug",
            "tasks",
            "is_completed",
        ]

    def get_is_completed(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        progress = LessonProgress.objects.filter(
            user=request.user,
            lesson=obj,
        ).first()

        return progress.is_completed if progress else False

class LessonShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "lesson_type", "slug", "order"]


class ModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)
    lessons = LessonShortSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "lessons_count", "lessons", "order"]


class CourseListSerializer(serializers.ModelSerializer):
    course_type = CourseTypeSerializer()
    teachers = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["title", "slug", "price", "image", "course_type", "teachers", "enrolled_count"]

    def get_teachers(self, obj):
        from apps.teachers.serializers import TeacherShortSerializer
        return TeacherShortSerializer(obj.teachers.all(), many=True).data

    def get_enrolled_count(self, obj):
        direct = UserCoursePurchase.objects.filter(course=obj).count()
        subscribed = CourseSubscription.objects.filter(course=obj, is_active=True).count()
        return direct + subscribed


class CourseDetailSerializer(serializers.ModelSerializer):
    course_type = CourseTypeSerializer()
    modules = ModuleSerializer(many=True, read_only=True)
    teachers = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "price", "image", "slug", "course_type", "teachers", "modules", "enrolled_count"]

    def get_teachers(self, obj):
        from apps.teachers.serializers import TeacherShortSerializer
        return TeacherShortSerializer(obj.teachers.all(), many=True).data

    def get_enrolled_count(self, obj):
        direct = UserCoursePurchase.objects.filter(course=obj).count()
        subscribed = CourseSubscription.objects.filter(course=obj, is_active=True).count()
        return direct + subscribed


class CourseSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSubscription
        fields = [
            "user", "course", "plan", "promo_code",
            "original_price", "final_price", "started_at", "expires_at", "is_active",
        ]


class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = ["code", "discount_percent", "is_active", "max_uses", "used_count", "valid_from", "valid_to", "is_valid"]

    def get_is_valid(self, obj):
        return obj.is_valid()


class CoursePlanSerializer(serializers.ModelSerializer):
    courses = CourseListSerializer(many=True, read_only=True)
    courses_count = serializers.IntegerField(source="courses.count", read_only=True)

    class Meta:
        model = CoursePlan
        fields = ["id", "title", "description", "duration_days", "price", "is_active", "courses", "courses_count"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = CoursePlanSerializer(read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            "id", "user", "plan", "promo_code",
            "original_price", "final_price", "subscribed_at", "expires_at", "is_active", "is_valid",
        ]
        read_only_fields = ["subscribed_at"]

    def get_is_valid(self, obj):
        return obj.is_valid


class CourseShortDetailSerializer(serializers.ModelSerializer):
    teachers = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "price", "image", "slug", "teachers"]

    def get_teachers(self, obj):
        from apps.teachers.serializers import TeacherShortSerializer
        return TeacherShortSerializer(obj.teachers.all(), many=True).data


class UserCoursePurchaseSerializer(serializers.ModelSerializer):
    course = CourseShortDetailSerializer(read_only=True)

    class Meta:
        model = UserCoursePurchase
        fields = ["id", "user", "course", "promo_code", "original_price", "final_price", "purchased_at"]
        read_only_fields = ["purchased_at"]


class CodeSubmissionSerializer(serializers.Serializer):
    language = serializers.CharField()
    code = serializers.CharField()


class SubmissionCreateSerializer(serializers.Serializer):
    code = serializers.CharField()
    language = serializers.CharField(max_length=50)


class SubmissionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["id", "language", "status", "result", "created_at"]
