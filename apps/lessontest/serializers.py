from rest_framework import serializers

from .models import LessonTest, TestAnswer, TestOption, TestQuestion, TestResult


class TestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOption
        fields = ["id", "text", "image", "order"]


class TestQuestionSerializer(serializers.ModelSerializer):
    options = TestOptionSerializer(many=True, read_only=True)

    class Meta:
        model = TestQuestion
        fields = ["id", "text", "image", "order", "options"]


class LessonTestSerializer(serializers.ModelSerializer):
    questions = TestQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = LessonTest
        fields = ["id", "title", "description", "duration_minutes", "pass_score", "questions_count", "questions"]


# --- Submit ---

class SubmitAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField(required=False, allow_null=True)


class SubmitTestSerializer(serializers.Serializer):
    answers = SubmitAnswerItemSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta javob bo'lishi kerak.")
        return value


# --- Result ---

class TestOptionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOption
        fields = ["id", "text", "image", "is_correct"]


class TestQuestionResultSerializer(serializers.ModelSerializer):
    options = TestOptionResultSerializer(many=True, read_only=True)

    class Meta:
        model = TestQuestion
        fields = ["id", "text", "image", "options"]


class TestAnswerDetailSerializer(serializers.ModelSerializer):
    question = TestQuestionResultSerializer(read_only=True)
    selected_option = TestOptionResultSerializer(read_only=True)

    class Meta:
        model = TestAnswer
        fields = ["question", "selected_option", "is_correct"]


class TestResultDetailSerializer(serializers.ModelSerializer):
    answers = TestAnswerDetailSerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source="test.lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="test.lesson.slug", read_only=True)
    test_title = serializers.CharField(source="test.title", read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id",
            "lesson_title",
            "lesson_slug",
            "test_title",
            "total_questions",
            "correct_count",
            "incorrect_count",
            "unanswered_count",
            "score_percent",
            "is_passed",
            "created_at",
            "answers",
        ]


class TestResultListSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="test.lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="test.lesson.slug", read_only=True)
    test_title = serializers.CharField(source="test.title", read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id",
            "lesson_title",
            "lesson_slug",
            "test_title",
            "total_questions",
            "correct_count",
            "incorrect_count",
            "unanswered_count",
            "score_percent",
            "is_passed",
            "created_at",
        ]
