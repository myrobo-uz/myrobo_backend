from django.contrib import admin

from .models import Competition, CompetitionParticipant


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "xp_reward", "is_published")
    list_filter = ("is_published", "start_date")
    search_fields = ("title", "description")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(CompetitionParticipant)
class CompetitionParticipantAdmin(admin.ModelAdmin):
    list_display = ("user", "competition", "status", "xp_awarded", "created_at")
    list_filter = ("status", "xp_awarded")
    search_fields = ("user__full_name", "competition__title")
    readonly_fields = ("created_at", "updated_at")
