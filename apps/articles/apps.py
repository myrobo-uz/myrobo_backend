from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    name = 'apps.articles'

    def ready(self):
        # Ensure modeltranslation translation options are registered
        try:
            from . import translation  # noqa: F401
        except Exception:
            pass
