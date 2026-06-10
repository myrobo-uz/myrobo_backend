from django.contrib import admin
from .models import User, UserDevice


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "telegram_id",
        "full_name",
        "phone_number",
        "balance",
        "is_blocked",
        "created_at",
        "is_admin"
    )

    list_filter = (
        "is_blocked",
        "created_at",
    )

    search_fields = (
        "telegram_id",
        "phone_number",
        "full_name",
        "telegram_username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "telegram_id",
                "telegram_username",
                "full_name",
                "phone_number",
                "avatar",
                "is_admin"
            )
        }),
        ("System Info", {
            "fields": (
                "balance",
                "is_blocked",
            )
        }),
        ("Meta", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "device_id",
        "ip",
        "is_active",
        "last_seen",
    )

    list_filter = (
        "is_active",
        "last_seen",
    )

    search_fields = (
        "device_id",
        "ip",
        "user__telegram_id",
        "user__full_name",
    )

    readonly_fields = (
        "last_seen",
    )