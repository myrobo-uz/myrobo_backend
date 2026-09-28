from django.contrib import admin

from .models import LoginLog, PageExit, UserActivity


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "ip", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__full_name", "user__phone_number", "ip"]
    readonly_fields = ["id", "user", "ip", "user_agent", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "anonymous_id", "action", "page", "description", "ip", "created_at"]
    list_filter = ["action", "page", "created_at"]
    search_fields = [
        "user__full_name", "user__phone_number", "anonymous_id", "description", "target_id", "ip",
    ]
    readonly_fields = [
        "id", "user", "anonymous_id", "action", "description", "page", "path",
        "target_type", "target_id", "meta", "ip", "user_agent", "created_at", "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PageExit)
class PageExitAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "anonymous_id", "page", "exit_reason", "time_spent", "ip", "created_at"]
    list_filter = ["exit_reason", "page", "created_at"]
    search_fields = ["user__full_name", "user__phone_number", "anonymous_id", "path", "ip"]
    readonly_fields = [
        "id", "user", "anonymous_id", "page", "path", "exit_reason", "time_spent",
        "ip", "user_agent", "created_at", "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
