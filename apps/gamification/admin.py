from django.contrib import admin

from .models import Certificate, Rank, XPLog


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ("title", "min_xp", "order")
    search_fields = ("title",)
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(XPLog)
class XPLogAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("user__full_name", "user__phone_number", "description")
    readonly_fields = (
        "id", "user", "amount", "reason", "description",
        "target_type", "target_id", "created_at", "updated_at",
    )

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "user", "course", "created_at")
    search_fields = ("certificate_number", "user__full_name", "course__title")
    readonly_fields = ("certificate_number", "created_at", "updated_at")
