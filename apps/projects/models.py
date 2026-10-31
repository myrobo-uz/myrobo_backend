from django.db import models

from apps.core.models import BaseModel
from apps.core.utils import SlugMixin
from apps.users.models import User


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Faol"
    COMPLETED = "completed", "Tugatilgan"
    ARCHIVED = "archived", "Arxivlangan"


class Project(BaseModel, SlugMixin):
    """Foydalanuvchi portfoliosidagi loyiha kartochkasi (simulyator bilan bog'lanishi mumkin)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="projects/images/", null=True, blank=True)
    tags = models.ManyToManyField("core.Tag", blank=True, related_name="projects")
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    simulator_ref = models.CharField(
        max_length=255, blank=True,
        help_text="Simulyatordagi tegishli loyiha identifikatori/havolasi",
    )
    board_type = models.CharField(
        max_length=64, blank=True, default="", help_text="masalan arduino-uno",
    )
    code = models.TextField(blank=True, default="", help_text="Asosiy .ino kodi")
    components_json = models.TextField(blank=True, default="", help_text="Diagramma komponentlari (JSON-matn)")
    wires_json = models.TextField(blank=True, default="", help_text="Simlar (JSON-matn)")
    files = models.JSONField(
        default=list, blank=True,
        help_text='[{"name": "sketch.ino", "content": "..."}]',
    )
    is_public = models.BooleanField(default=True, help_text="Ochiq yoki shaxsiy")
    views = models.BigIntegerField(default=0)

    class Meta:
        db_table = "projects_project"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
