from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

from apps.core.models import BaseModel
from apps.core.utils import SlugMixin
from apps.users.models import User


class Topic(BaseModel, SlugMixin):
    """Forum mavzusi — maqolaga o'xshash, lekin muhokama (izoh + like) uchun."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = RichTextUploadingField()
    tags = models.ManyToManyField("core.Tag", blank=True, related_name="topics")
    is_solved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    views = models.BigIntegerField(default=0)

    class Meta:
        db_table = "community_topic"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_solved"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TopicLike(BaseModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topic_likes")

    class Meta:
        db_table = "community_topic_like"
        constraints = [models.UniqueConstraint(fields=["topic", "user"], name="unique_topic_like")]

    def __str__(self):
        return f"{self.user_id} ♥ {self.topic_id}"


class TopicComment(BaseModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topic_comments")
    text = models.TextField()
    is_accepted = models.BooleanField(default=False, help_text="Mavzu egasi tomonidan yechim deb belgilangan")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "community_topic_comment"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["topic", "is_active"])]

    def __str__(self):
        return f"{self.user_id} - {self.topic_id}"


class CommentLike(BaseModel):
    comment = models.ForeignKey(TopicComment, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_likes")

    class Meta:
        db_table = "community_comment_like"
        constraints = [models.UniqueConstraint(fields=["comment", "user"], name="unique_comment_like")]

    def __str__(self):
        return f"{self.user_id} ♥ {self.comment_id}"
