from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = 'apps.courses'

    def ready(self):
        try:
            from . import translation  # noqa: F401
        except Exception:
            pass
