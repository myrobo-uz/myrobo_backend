from django.contrib import admin

from .models import LessonTest, TestAnswer, TestOption, TestQuestion, TestResult


class TestOptionInline(admin.TabularInline):
    model = TestOption
    extra = 2
    fields = ["text", "image", "is_correct", "order"]


class TestQuestionInline(admin.StackedInline):
    model = TestQuestion
    extra = 1
    fields = ["text", "image", "order"]
    show_change_link = True


@admin.register(LessonTest)
class LessonTestAdmin(admin.ModelAdmin):
    list_display = ["title", "lesson", "pass_score", "duration_minutes", "created_at"]
    search_fields = ["title", "lesson__title"]
    inlines = [TestQuestionInline]


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "test", "order", "created_at"]
    list_filter = ["test"]
    inlines = [TestOptionInline]


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ["user", "test", "correct_count", "incorrect_count", "unanswered_count", "score_percent", "is_passed", "created_at"]
    list_filter = ["is_passed", "test"]
    search_fields = ["user__full_name", "test__title"]
    readonly_fields = ["user", "test", "total_questions", "correct_count", "incorrect_count", "unanswered_count", "score_percent", "is_passed"]
