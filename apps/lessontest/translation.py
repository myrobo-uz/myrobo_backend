from modeltranslation.translator import register, TranslationOptions

from .models import LessonTest, TestQuestion, TestOption


@register(LessonTest)
class LessonTestTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(TestQuestion)
class TestQuestionTranslationOptions(TranslationOptions):
    fields = ("text",)


@register(TestOption)
class TestOptionTranslationOptions(TranslationOptions):
    fields = ("text",)
