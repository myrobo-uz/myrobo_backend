from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import BaseModel


PHONE_VALIDATOR = RegexValidator(regex=r"^\+?\d+$")


class User(BaseModel):
    telegram_id = models.BigIntegerField(unique=True)
    phone_number = models.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    telegram_username = models.CharField(max_length=256, null=True, blank=True)
    full_name = models.CharField(max_length=256)
    avatar = models.ImageField(upload_to="users/avatars/", null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_blocked = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["telegram_id"]),
            models.Index(fields=["is_blocked"]),
        ]

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class UserDevice(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    user_agent = models.TextField()
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "users_userdevice"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]
