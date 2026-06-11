from decimal import Decimal

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Lesson
from apps.users.authentication import CustomJWTAuthentication

from .models import LessonTest, TestAnswer, TestOption, TestQuestion, TestResult
from .serializers import (
    LessonTestSerializer,
    SubmitTestSerializer,
    TestResultDetailSerializer,
    TestResultListSerializer,
)


def _check_lesson_access(user, lesson):
    from django.utils import timezone
    from apps.courses.models import UserCoursePurchase, UserSubscription

    course = lesson.module.course
    if UserCoursePurchase.objects.filter(user=user, course=course).exists():
        return True
    return UserSubscription.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now(),
        plan__courses=course,
    ).exists()


@extend_schema(tags=["Lesson Test"], summary="Darsga tegishli testni olish")
class LessonTestDetailView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_slug):
        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"), slug=lesson_slug
        )
        if not _check_lesson_access(request.user, lesson):
            return Response(
                {"detail": "Bu darsga kirish huquqingiz yo'q."},
                status=status.HTTP_403_FORBIDDEN,
            )
        test = get_object_or_404(
            LessonTest.objects.prefetch_related("questions__options"), lesson=lesson
        )
        serializer = LessonTestSerializer(test)
        return Response(serializer.data)


@extend_schema(tags=["Lesson Test"], summary="Test javoblarini yuborish va natijani olish")
class SubmitTestView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_slug):
        lesson = get_object_or_404(
            Lesson.objects.select_related("module__course"), slug=lesson_slug
        )
        if not _check_lesson_access(request.user, lesson):
            return Response(
                {"detail": "Bu darsga kirish huquqingiz yo'q."},
                status=status.HTTP_403_FORBIDDEN,
            )
        test = get_object_or_404(LessonTest, lesson=lesson)

        existing_passed = (
            TestResult.objects.filter(user=request.user, test=test, is_passed=True)
            .order_by("-created_at")
            .first()
        )
        if existing_passed:
            result_data = TestResultDetailSerializer(existing_passed).data
            return Response(
                {
                    "detail": "Siz avval ushbu testdan o'tgansiz.",
                    "result": result_data,
                },
                status=status.HTTP_200_OK,
            )

        serializer = SubmitTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data["answers"]

        questions = list(
            TestQuestion.objects.filter(test=test).prefetch_related("options")
        )
        question_map = {str(q.id): q for q in questions}
        total = len(questions)

        answered_question_ids = {str(a["question_id"]) for a in submitted_answers}
        for qid in list(question_map.keys()):
            if qid not in answered_question_ids:
                submitted_answers.append({"question_id": qid, "option_id": None})

        correct = 0
        incorrect = 0
        unanswered = 0
        answer_objects = []

        for item in submitted_answers:
            qid = str(item["question_id"])
            question = question_map.get(qid)
            if question is None:
                continue
            option_id = item.get("option_id")
            selected_option = None
            is_correct = False
            if option_id:
                selected_option = TestOption.objects.filter(
                    id=option_id, question=question
                ).first()
                if selected_option:
                    is_correct = selected_option.is_correct
                    if is_correct:
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    unanswered += 1
            else:
                unanswered += 1
            answer_objects.append(
                TestAnswer(
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct,
                )
            )

        score_percent = Decimal(correct) / Decimal(total) * 100 if total > 0 else Decimal(0)
        is_passed = score_percent >= test.pass_score
        result = TestResult.objects.create(
            user=request.user,
            test=test,
            total_questions=total,
            correct_count=correct,
            incorrect_count=incorrect,
            unanswered_count=unanswered,
            score_percent=score_percent.quantize(Decimal("0.01")),
            is_passed=is_passed,
        )
        for ans in answer_objects:
            ans.result = result
        TestAnswer.objects.bulk_create(answer_objects)

        result_data = TestResultDetailSerializer(result).data
        return Response(result_data, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Lesson Test"], summary="Foydalanuvchining barcha test natijalari")
class TestResultListView(ListAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TestResultListSerializer

    def get_queryset(self):
        return (
            TestResult.objects.filter(user=self.request.user)
            .select_related("test__lesson")
        )


@extend_schema(tags=["Lesson Test"], summary="Test natijasi tafsiloti")
class TestResultDetailView(RetrieveAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TestResultDetailSerializer

    def get_object(self):
        return get_object_or_404(
            TestResult.objects.filter(user=self.request.user)
            .select_related("test__lesson")
            .prefetch_related(
                "answers__question__options",
                "answers__selected_option",
            ),
            id=self.kwargs["result_id"],
        )
