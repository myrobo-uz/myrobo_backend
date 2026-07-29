from django.utils import translation
from django.conf import settings


class QueryLanguageMiddleware:
    """Middleware to set language from ?lang query param or Accept-Language header.

    Priority: if ?lang is provided and valid, it will be used. Otherwise the first
    language from Accept-Language will be used if supported. Falls back to
    settings.LANGUAGE_CODE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = None
        # Query param takes precedence
        qlang = request.GET.get("lang")
        if qlang:
            lang = qlang.strip()[:2]
        else:
            # Accept-Language header (may contain q values)
            al = request.headers.get("Accept-Language", "")
            if al:
                # take primary language tag
                lang = al.split(",")[0].strip()[:2]

        if lang and lang in {code for code, _ in settings.LANGUAGES}:
            translation.activate(lang)
            request.LANGUAGE_CODE = translation.get_language()
        else:
            translation.activate(settings.LANGUAGE_CODE)
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE

        response = self.get_response(request)
        translation.deactivate()
        return response
