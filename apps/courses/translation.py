from modeltranslation.translator import register, TranslationOptions

from .models import (
    CourseType,
    Course,
    Module,
    Lesson,
    LessonTask,
    CoursePlan,
    Company,
)


@register(CourseType)
class CourseTypeTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Course)
class CourseTranslationOptions(TranslationOptions):
    fields = ("title", "description",)


@register(Module)
class ModuleTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Lesson)
class LessonTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(LessonTask)
class LessonTaskTranslationOptions(TranslationOptions):
    fields = ("title", "description", "statement")


@register(CoursePlan)
class CoursePlanTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(Company)
class CompanyTranslationOptions(TranslationOptions):
    fields = ("name", "description")

