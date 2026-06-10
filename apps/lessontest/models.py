from django.db import models

from apps.core.models import BaseModel
from apps.courses.models import Lesson
from apps.users.models import User


class LessonTest(BaseModel):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="test")
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    pass_score = models.PositiveIntegerField(default=60, help_text="O'tish uchun minimal foiz")

    def __str__(self):
        return f"{self.lesson.title} — {self.title}"


class TestQuestion(BaseModel):
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="lessontest/questions/", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Savol: {self.text[:60] or 'rasm'}"


class TestOption(BaseModel):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="lessontest/options/", null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Variant: {self.text[:60] or 'rasm'} ({'to\'g\'ri' if self.is_correct else 'noto\'g\'ri'})"


class TestResult(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_results")
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE, related_name="results")
    total_questions = models.PositiveIntegerField()
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    score_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "test"])]

    def __str__(self):
        return f"{self.user.full_name} — {self.test.title} ({self.score_percent}%)"


class TestAnswer(BaseModel):
    result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="user_answers")
    selected_option = models.ForeignKey(
        TestOption, on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_by"
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ("result", "question")

    def __str__(self):
        return f"Javob: {'to\'g\'ri' if self.is_correct else 'noto\'g\'ri'}"
