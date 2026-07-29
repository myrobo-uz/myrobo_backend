from django.apps import AppConfig


class TeachersConfig(AppConfig):
    name = 'apps.teachers'

    def ready(self):
        try:
            from . import translation  # noqa: F401
        except Exception:
            pass
