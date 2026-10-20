from django.db import models
import uuid

from apps.core.utils import SlugMixin


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True,)
    updated_at = models.DateTimeField(auto_now=True,)
    deleted_at = models.DateTimeField(null=True,blank=True,db_index=True,)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "created_at"


class Contact(BaseModel):
    name = models.CharField(max_length=256, verbose_name="Ism")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Xabar")
    image = models.ImageField(upload_to="contacts/images/", null=True, blank=True, verbose_name="Rasm")

    class Meta:
        db_table = "core_contact"
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"

    def __str__(self):
        return f"{self.name} | {self.email}"


class Tag(BaseModel, SlugMixin):
    """Umumiy teg — kurslar, maqolalar va boshqa modullar tomonidan qayta ishlatiladi."""

    slug_field = "name"

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        db_table = "core_tag"
        ordering = ["name"]
        verbose_name = "Teg"
        verbose_name_plural = "Teglar"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

