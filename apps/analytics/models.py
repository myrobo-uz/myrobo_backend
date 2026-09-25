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
    COURSE_VIEW = "course_view", "Kursni ko'rish"
    LESSON_VIEW = "lesson_view", "Darsni ko'rish"
    LESSON_COMPLETE = "lesson_complete", "Darsni yakunlash"
    COURSE_PURCHASE = "course_purchase", "Kurs/obuna sotib olish"
    TASK_SUBMIT = "task_submit", "Kod topshiriq yuborish"
    TEST_SUBMIT = "test_submit", "Test topshirish"
    ARTICLE_VIEW = "article_view", "Maqolani ko'rish"
    PROFILE_UPDATE = "profile_update", "Profilni yangilash"
    OTHER = "other", "Boshqa"


class UserActivity(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=30, choices=ActivityType.choices)
    description = models.CharField(max_length=255, blank=True)
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
        ]

    def __str__(self):
        return f"{self.user.full_name} — {self.get_action_display()} @ {self.created_at:%Y-%m-%d %H:%M}"
