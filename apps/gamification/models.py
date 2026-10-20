import secrets
import string

from django.db import models

from apps.core.models import BaseModel
from apps.core.utils import SlugMixin
from apps.courses.models import Course
from apps.users.models import User


class Rank(BaseModel, SlugMixin):
    """Admin tomonidan belgilanadigan daraja bosqichlari (masalan: Boshlovchi, O'rta, Ekspert)."""

    slug_field = "title"

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    min_xp = models.PositiveIntegerField(unique=True, help_text="Shu XP'ga yetgan foydalanuvchi shu darajaga ega bo'ladi")
    icon = models.ImageField(upload_to="gamification/ranks/", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "gamification_rank"
        ordering = ["min_xp"]
        verbose_name = "Rank"
        verbose_name_plural = "Ranklar"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.min_xp} XP)"


class XPReason(models.TextChoices):
    LESSON_COMPLETE = "lesson_complete", "Darsni yakunlash"
    COURSE_COMPLETE = "course_complete", "Kursni to'liq tugatish"
    TEST_PASSED = "test_passed", "Testdan o'tish"
    PROJECT_COMPLETE = "project_complete", "Loyihani yakunlash"
    COMPETITION_WIN = "competition_win", "Musobaqada g'olib bo'lish"
    MANUAL = "manual", "Admin tomonidan qo'lda"
    OTHER = "other", "Boshqa"


class XPLog(BaseModel):
    """XP yozuvlari tarixi — audit va hisob-kitob uchun."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xp_logs")
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=30, choices=XPReason.choices)
    description = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "gamification_xp_log"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user.full_name} +{self.amount} XP ({self.get_reason_display()})"


def _generate_certificate_number() -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        candidate = "MR-" + "".join(secrets.choice(chars) for _ in range(10))
        if not Certificate.objects.filter(certificate_number=candidate).exists():
            return candidate


class Certificate(BaseModel):
    """Kurs 100% tugatilganda avtomatik beriladigan sertifikat."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    certificate_number = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        db_table = "gamification_certificate"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_user_course_certificate"),
        ]

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = _generate_certificate_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.certificate_number} — {self.user.full_name} / {self.course.title}"
