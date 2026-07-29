from django.apps import AppConfig


class LessontestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lessontest'

    def ready(self):
        try:
            from . import translation  # noqa: F401
        except Exception:
            pass
