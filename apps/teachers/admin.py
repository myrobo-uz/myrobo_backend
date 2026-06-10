from django.contrib import admin

from apps.teachers.models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "username",
        "job",
        "work_place",
        "created_at",
    )

    list_display_links = (
        "id",
        "full_name",
    )

    search_fields = (
        "first_name",
        "last_name",
        "middle_name",
        "username",
        "job",
    )

    list_filter = (
        "job",
        "created_at",
    )

    prepopulated_fields = {
        "slug": ("username",)
    }

    filter_horizontal = (
        "courses",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "first_name",
        "last_name",
    )

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "middle_name",
                    "username",
                    "slug",
                    "image",
                )
            },
        ),
        (
            "Professional Information",
            {
                "fields": (
                    "job",
                    "direction",
                    "experience",
                    "work_place",
                    "about",
                )
            },
        ),
        (
            "Courses",
            {
                "fields": (
                    "courses",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Full Name")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"