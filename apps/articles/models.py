from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel
from apps.users.models import User


def _unique_slug(model_cls, base):
    slug = base
    counter = 1
    while model_cls.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class ArticleType(BaseModel):
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=300, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(ArticleType, slugify(self.title))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Articles(BaseModel):
    type = models.ForeignKey(
        ArticleType, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = RichTextUploadingField()
    image = models.ImageField(upload_to="articles/images")
    views = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "type"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Articles, slugify(self.title))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(BaseModel):
    article = models.ForeignKey(Articles, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["article", "is_active"])]

    def __str__(self):
        return f"{self.user_id} - {self.article_id}"
