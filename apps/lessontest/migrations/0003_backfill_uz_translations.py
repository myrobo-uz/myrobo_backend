# 0002 added empty title_uz/description_uz/text_uz columns. modeltranslation
# makes the base field (title/description/text) proxy to the *_uz column for
# the default "uz" language, so without this backfill every existing lesson
# test/question/option would suddenly appear blank. This copies the original
# values into the new _uz columns for rows created before 0002.

from django.db import migrations
from django.db.models import F


def backfill_uz(apps, schema_editor):
    LessonTest = apps.get_model('lessontest', 'LessonTest')
    TestQuestion = apps.get_model('lessontest', 'TestQuestion')
    TestOption = apps.get_model('lessontest', 'TestOption')

    LessonTest.objects.filter(title_uz__isnull=True).update(title_uz=F('title'))
    LessonTest.objects.filter(description_uz__isnull=True).update(description_uz=F('description'))
    TestQuestion.objects.filter(text_uz__isnull=True).update(text_uz=F('text'))
    TestOption.objects.filter(text_uz__isnull=True).update(text_uz=F('text'))


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('lessontest', '0002_lessontest_translations'),
    ]

    operations = [
        migrations.RunPython(backfill_uz, noop_reverse),
    ]
