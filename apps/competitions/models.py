from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.core.utils import SlugMixin
from apps.users.models import User


class Competition(BaseModel, SlugMixin):
    """Musobaqa — faol/tugagan holati start/end sanalaridan hisoblanadi."""

    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True, help_text="Asosiy talablar")
    image = models.ImageField(upload_to="competitions/images/", null=True, blank=True)
    directions = models.ManyToManyField("core.Tag", blank=True, related_name="competitions")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    xp_reward = models.PositiveIntegerField(default=0, help_text="G'olibga beriladigan XP")
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="authored_competitions"
    )

    class Meta:
        db_table = "competitions_competition"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    @property
    def status(self) -> str:
        now = timezone.now()
        if now < self.start_date:
            return "upcoming"
        if now > self.end_date:
            return "finished"
        return "active"

    def __str__(self):
        return self.title


class ParticipantStatus(models.TextChoices):
    REGISTERED = "registered", "Ro'yxatdan o'tgan"
    SUBMITTED = "submitted", "Topshirgan"
    WINNER = "winner", "G'olib"


class CompetitionParticipant(BaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="competition_participations")
    status = models.CharField(max_length=20, choices=ParticipantStatus.choices, default=ParticipantStatus.REGISTERED)
    submission_note = models.TextField(blank=True)
    xp_awarded = models.BooleanField(default=False)

    class Meta:
        db_table = "competitions_participant"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["competition", "user"], name="unique_competition_participant"),
        ]
        indexes = [models.Index(fields=["competition", "status"])]

    def __str__(self):
        return f"{self.user.full_name} — {self.competition.title} ({self.status})"
