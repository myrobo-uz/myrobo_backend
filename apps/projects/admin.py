from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "views", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "user__full_name")
    readonly_fields = ("slug", "views", "created_at", "updated_at")
