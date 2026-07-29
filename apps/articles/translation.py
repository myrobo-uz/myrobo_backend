from modeltranslation.translator import register, TranslationOptions

from .models import ArticleType, Articles


@register(ArticleType)
class ArticleTypeTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Articles)
class ArticlesTranslationOptions(TranslationOptions):
    fields = ("title", "description")
