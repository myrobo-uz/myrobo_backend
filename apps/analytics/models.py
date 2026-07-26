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
