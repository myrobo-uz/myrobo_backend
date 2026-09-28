from django.db import models

from apps.core.models import BaseModel
from apps.users.models import User


class LoginLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_logs")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "analytics_login_log"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user.full_name} @ {self.created_at:%Y-%m-%d %H:%M}"


class ActivityType(models.TextChoices):
    LOGIN = "login", "Kirish"
    PAGE_VIEW = "page_view", "Sahifani ko'rish"
    COURSE_VIEW = "course_view", "Kursni ko'rish"
    LESSON_VIEW = "lesson_view", "Darsni ko'rish"
    LESSON_COMPLETE = "lesson_complete", "Darsni yakunlash"
    COURSE_PURCHASE = "course_purchase", "Kurs/obuna sotib olish"
    TASK_SUBMIT = "task_submit", "Kod topshiriq yuborish"
    TEST_SUBMIT = "test_submit", "Test topshirish"
    ARTICLE_VIEW = "article_view", "Maqolani ko'rish"
    PROFILE_UPDATE = "profile_update", "Profilni yangilash"
    OTHER = "other", "Boshqa"


class ExitReason(models.TextChoices):
    NAVIGATION = "navigation", "Ichki navigatsiya"
    TAB_CLOSE = "tab_close", "Tab yopildi"
    BROWSER_CLOSE = "browser_close", "Brauzer yopildi"
    LOGOUT = "logout", "Tizimdan chiqish"
    IDLE = "idle", "Faolsizlik"
    UNKNOWN = "unknown", "Noma'lum"


class UserActivity(BaseModel):
    # Login qilgan foydalanuvchi uchun to'ldiriladi; anonim foydalanuvchi uchun NULL
    # (o'rniga anonymous_id ishlatiladi).
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    anonymous_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=30, choices=ActivityType.choices)
    description = models.CharField(max_length=255, blank=True)
    page = models.CharField(max_length=100, blank=True)
    path = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "analytics_user_activity"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["anonymous_id", "created_at"]),
            models.Index(fields=["page", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | ~models.Q(anonymous_id=""),
                name="useractivity_user_or_anonymous_id",
            ),
        ]

    def __str__(self):
        who = self.user.full_name if self.user_id else f"anon:{self.anonymous_id}"
        return f"{who} — {self.get_action_display()} @ {self.created_at:%Y-%m-%d %H:%M}"


class PageExit(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="page_exits"
    )
    anonymous_id = models.CharField(max_length=64, blank=True, db_index=True)
    page = models.CharField(max_length=100)
    path = models.CharField(max_length=255, blank=True)
    exit_reason = models.CharField(
        max_length=20, choices=ExitReason.choices, default=ExitReason.UNKNOWN
    )
    time_spent = models.PositiveIntegerField(default=0, help_text="Sekundlarda")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "analytics_page_exit"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["page", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["anonymous_id", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | ~models.Q(anonymous_id=""),
                name="pageexit_user_or_anonymous_id",
            ),
        ]

    def __str__(self):
        who = self.user.full_name if self.user_id else f"anon:{self.anonymous_id}"
        return f"{who} — {self.page} ({self.time_spent}s, {self.exit_reason})"
