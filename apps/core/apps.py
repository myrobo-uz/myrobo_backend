from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'apps.core'

    def ready(self):
        try:
            from . import translation  # noqa: F401
        except Exception:
            pass
