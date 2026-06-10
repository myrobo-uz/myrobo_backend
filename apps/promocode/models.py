import random
import string

from django.db import models
from apps.core.models import BaseModel


class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Korxona nomi")
    description = models.TextField(blank=True, default="", verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        db_table = "promocode_company"
        verbose_name = "Korxona"
        verbose_name_plural = "Korxonalar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class PromoCode(BaseModel):
    DISCOUNT_TYPE_PERCENT = "percent"
    DISCOUNT_TYPE_FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENT, "Foiz (%)"),
        (DISCOUNT_TYPE_FIXED, "Qat'iy summa (so'm)"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="promocodes",
        verbose_name="Korxona",
    )
    code = models.CharField(max_length=32, unique=True, verbose_name="Kod")
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default=DISCOUNT_TYPE_PERCENT,
        verbose_name="Chegirma turi",
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Chegirma miqdori"
    )
    max_uses = models.PositiveIntegerField(default=1, verbose_name="Maksimal foydalanish")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Foydalanilgan marta")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Amal qilish muddati")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        db_table = "promocode_code"
        verbose_name = "Promokod"
        verbose_name_plural = "Promokodlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.company.name})"

    @staticmethod
    def generate_code(length=8, prefix=""):
        chars = string.ascii_uppercase + string.digits
        code = "".join(random.choices(chars, k=length))
        return f"{prefix}{code}" if prefix else code
