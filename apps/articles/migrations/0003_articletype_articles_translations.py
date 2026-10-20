# NOTE: Production actually never had these modeltranslation columns, despite
# apps/articles/translation.py registering them for a long time. 0001_initial
# incorrectly assumed they already existed (matching the pattern seen in other
# apps) and was applied with --fake, which only recorded it as "done" without
# creating these columns. This migration genuinely creates them and must be
# applied for REAL (no --fake) to fix the live "column ... does not exist" 500s.

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0002_articles_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='articletype',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articletype',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articletype',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='description_uz',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='description_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
        migrations.AddField(
            model_name='articles',
            name='description_ru',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
    ]
