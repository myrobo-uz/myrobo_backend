from modeltranslation.translator import register, TranslationOptions

from .models import Teacher


@register(Teacher)
class TeacherTranslationOptions(TranslationOptions):
    # names typically shouldn't be translated, but biography-like fields should
    fields = ("job", "about", "direction", "experience", "work_place")
