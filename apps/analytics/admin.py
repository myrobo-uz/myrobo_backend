from django.contrib import admin

from .models import LoginLog, UserActivity


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
    list_display = ["id", "user", "action", "description", "ip", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["user__full_name", "user__phone_number", "description", "target_id"]
    readonly_fields = [
        "id", "user", "action", "description", "target_type", "target_id",
        "meta", "ip", "user_agent", "created_at", "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
