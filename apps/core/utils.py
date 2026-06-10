from urllib.parse import urlparse

from django.utils.text import slugify


class SlugMixin:
    slug_field = "title"

    def generate_unique_slug(self):
        base_slug = slugify(getattr(self, self.slug_field))
        slug = base_slug
        counter = 1
        ModelClass = self.__class__
        while ModelClass.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


def kinescope_to_embed(url: str):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        video_id = parsed.path.strip("/").split("/")[-1]
        return f"https://kinescope.io/embed/{video_id}"
    except Exception:
        return url
