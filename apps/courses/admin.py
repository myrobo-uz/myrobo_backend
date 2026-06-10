from django.contrib import admin
from .models import (
    Company,
    CourseType,
    Course,
    Module,
    Lesson,
    LessonTask,
    TaskTestCase,
    LessonProgress,
    Submission,
    CoursePlan,
    PromoCode,
    CourseSubscription,
    CourseTelegramLink,
    UserSubscription,
)
from django.utils import timezone

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    show_change_link = True
    fields = ("order", "title", "slug")
    ordering = ("order",)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    show_change_link = True
    fields = ("order", "title", "lesson_type", "slug")
    ordering = ("order",)


class LessonTaskInline(admin.TabularInline):
    model = LessonTask
    extra = 0
    show_change_link = True


class TaskTestCaseInline(admin.TabularInline):
    model = TaskTestCase
    extra = 0


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "course_type", "price", "slug", "created_at")
    list_filter = ("course_type",)
    search_fields = ("title", "description", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ModuleInline]
    list_select_related = ("course_type",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "course", "slug", "created_at")
    list_display_links = ("title",)
    list_editable = ("order",)
    search_fields = ("title", "slug")
    list_filter = ("course",)
    ordering = ("course", "order")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]
    list_select_related = ("course",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "module", "lesson_type", "slug", "created_at")
    list_display_links = ("title",)
    list_editable = ("order",)
    list_filter = ("lesson_type", "module__course")
    search_fields = ("title", "description", "slug")
    ordering = ("module", "order")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonTaskInline]
    list_select_related = ("module",)


@admin.register(LessonTask)
class LessonTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson")
    search_fields = ("title", "statement")
    list_filter = ("lesson",)
    inlines = [TaskTestCaseInline]
    list_select_related = ("lesson",)


@admin.register(TaskTestCase)
class TaskTestCaseAdmin(admin.ModelAdmin):
    list_display = ("task", "is_hidden")
    list_filter = ("is_hidden",)
    search_fields = ("task__title",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "is_completed", "completed_at")
    list_filter = ("is_completed",)
    search_fields = ("user__username", "lesson__title")
    list_select_related = ("user", "lesson")



@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "status", "language", "created_at")
    list_filter = ("status", "language")
    search_fields = ("user__username", "task__title")
    list_select_related = ("user", "task")



@admin.register(CoursePlan)
class CoursePlanAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "duration_days", "is_active")
    search_fields = ("title", "course__title")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "company", "discount_percent", "is_active", "used_count", "max_uses")
    list_filter = ("is_active", "company")
    search_fields = ("code", "company__name")
    autocomplete_fields = ("company",)



@admin.register(CourseSubscription)
class CourseSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "plan",
        "final_price",
        "is_active",
        "expires_at",
    )
    list_filter = ("is_active", "course")
    search_fields = ("user__username", "course__title")
    list_select_related = ("user", "course", "plan")

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "original_price",
        "final_price",
        "is_active",
        "is_valid_status",
        "subscribed_at",
        "expires_at",
    )

    list_filter = (
        "is_active",
        "subscribed_at",
        "expires_at",
        "plan",
    )

    search_fields = (
        "user__full_name",
        "user__phone_number",
        "plan__title",
    )

    readonly_fields = (
        "subscribed_at",
        "is_valid_status",
    )

    autocomplete_fields = (
        "user",
        "plan",
        "promo_code",
    )

    ordering = ("-subscribed_at",)

    fieldsets = (
        ("Subscription Info", {
            "fields": (
                "user",
                "plan",
                "promo_code",
            )
        }),
        ("Pricing", {
            "fields": (
                "original_price",
                "final_price",
            )
        }),
        ("Status", {
            "fields": (
                "is_active",
                "is_valid_status",
                "subscribed_at",
                "expires_at",
            )
        }),
    )

    @admin.display(boolean=True, description="Valid")
    def is_valid_status(self, obj):
        return obj.is_active and obj.expires_at > timezone.now()
    
admin.site.register(CourseTelegramLink)