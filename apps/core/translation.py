from modeltranslation.translator import register, TranslationOptions

from .models import Contact


@register(Contact)
class ContactTranslationOptions(TranslationOptions):
    fields = ("name", "message")
