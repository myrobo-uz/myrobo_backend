from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel
from apps.courses.models import Course


class Teacher(BaseModel):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    middle_name = models.CharField(max_length=256)
    username = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    job = models.CharField(max_length=255)
    about = models.TextField()
    direction = models.CharField(max_length=255, blank=True)
    experience = models.CharField(max_length=255, blank=True)
    work_place = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="teachers/images/")
    courses = models.ManyToManyField(
        Course,
        related_name="teachers",
        blank=True,
    )

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.username)

        super().save(*args, **kwargs)