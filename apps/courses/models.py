from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.core.utils import SlugMixin
from apps.users.models import User


class CourseType(BaseModel, SlugMixin):
    title = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Course(BaseModel, SlugMixin):
    course_type = models.ForeignKey(
        CourseType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    title = models.CharField(max_length=256)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="course/images")
    slug = models.SlugField(unique=True, blank=True)
    views = models.BigIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["course_type"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def user_has_access(self, user):
        if UserCoursePurchase.objects.filter(user=user, course=self).exists():
            return True
        active = UserSubscription.objects.filter(
            user=user, is_active=True, expires_at__gt=timezone.now()
        ).values_list("plan_id", flat=True)
        return CoursePlan.objects.filter(id__in=list(active), courses=self).exists()

    def __str__(self):
        return self.title


class CourseTelegramLink(BaseModel):
    class LinkType(models.TextChoices):
        CHANNEL = "channel", "Kanal"
        GROUP = "group", "Gruppa"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="telegram_links")
    title = models.CharField(max_length=256)
    chat_id = models.BigIntegerField()
    link_type = models.CharField(max_length=10, choices=LinkType.choices, default=LinkType.GROUP)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("course", "chat_id")
        indexes = [models.Index(fields=["course", "is_active"])]

    def __str__(self):
        return f"{self.course.title} → {self.title} ({self.chat_id})"


class Module(BaseModel, SlugMixin):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(BaseModel, SlugMixin):
    class LessonType(models.TextChoices):
        CONTENT = "content", "Content"
        CODE = "code", "Code"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    lesson_type = models.CharField(max_length=10, choices=LessonType.choices)
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    video_url = models.CharField(max_length=500, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LessonProgress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    is_completed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "lesson"], name="unique_user_lesson_progress")
        ]
        indexes = [models.Index(fields=["user", "is_completed"])]

    
import re

def slugify_title(title):
    title = title.lower().strip()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[\s_-]+', '_', title)
    return title

def lesson_sample_input_path(instance, filename):
    name = slugify_title(instance.title)
    return f"courses/task_{name}/{filename}"

def lesson_sample_output_path(instance, filename):
    name = slugify_title(instance.title)
    return f"courses/task_{name}/{filename}"

def testcase_input_upload_path(instance, filename):
    name = slugify_title(instance.task.title)
    return f"courses/task_{name}/{filename}"

def testcase_output_upload_path(instance, filename):
    name = slugify_title(instance.task.title)
    return f"courses/task_{name}/{filename}"


class LessonTask(BaseModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField()
    statement = models.TextField()
    sample_input = models.FileField(upload_to=lesson_sample_input_path)
    sample_output = models.FileField(upload_to=lesson_sample_output_path)

    def __str__(self):
        return self.title

class TaskTestCase(BaseModel):
    task = models.ForeignKey(LessonTask, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.FileField(upload_to=testcase_input_upload_path)
    expected_output = models.FileField(upload_to=testcase_output_upload_path)
    is_hidden = models.BooleanField(default=False)


class SubmissionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    WRONG = "wrong", "Wrong"
    ERROR = "error", "Error"


class Submission(BaseModel):
    task = models.ForeignKey(LessonTask, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING
    )
    result = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status"])]


class CoursePlan(BaseModel):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    courses = models.ManyToManyField(Course, related_name="subscription_plans")
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.duration_days} days)"


class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Korxona nomi")
    description = models.TextField(blank=True, default="", verbose_name="Tavsif")

    class Meta:
        db_table = "courses_company"
        verbose_name = "Korxona"
        verbose_name_plural = "Korxonalar"

    def __str__(self):
        return self.name


class PromoCode(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promocodes",
        verbose_name="Korxona",
    )
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True


class UserSubscription(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(CoursePlan, on_delete=models.CASCADE, related_name="user_subscriptions")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-subscribed_at",)
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["is_active", "expires_at"]),
        ]

    @property
    def is_valid(self):
        return self.is_active and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.user.full_name} - {self.plan.title}"


class UserCoursePurchase(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchased_courses")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="buyers")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ("-purchased_at",)
        indexes = [models.Index(fields=["user", "course"])]

    def __str__(self):
        return f"{self.user.full_name} - {self.course.title}"


class CourseSubscription(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    plan = models.ForeignKey(CoursePlan, on_delete=models.SET_NULL, null=True)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "course", "is_active"]),
            models.Index(fields=["is_active", "expires_at"]),
        ]

    @property
    def is_valid(self):
        return self.is_active and self.expires_at > timezone.now()
