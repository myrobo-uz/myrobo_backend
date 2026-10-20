# NOTE: These fields were already added to production by django-modeltranslation
# (see apps/courses/translation.py) but this app never had a committed migration
# for them. This file is meant to be applied with --fake in production since the
# columns already exist there; genuinely new schema goes in 0004.

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_course_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='description_en',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Tavsif'),
        ),
        migrations.AddField(
            model_name='company',
            name='description_ru',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Tavsif'),
        ),
        migrations.AddField(
            model_name='company',
            name='description_uz',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Tavsif'),
        ),
        migrations.AddField(
            model_name='company',
            name='name_en',
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name='Korxona nomi'),
        ),
        migrations.AddField(
            model_name='company',
            name='name_ru',
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name='Korxona nomi'),
        ),
        migrations.AddField(
            model_name='company',
            name='name_uz',
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name='Korxona nomi'),
        ),
        migrations.AddField(
            model_name='course',
            name='description_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='description_ru',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='description_uz',
            field=ckeditor_uploader.fields.RichTextUploadingField(null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='description_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='description_ru',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='description_uz',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='title_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='title_ru',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='title_uz',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='coursetype',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='coursetype',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='coursetype',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='description_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='description_ru',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='description_uz',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='description_ru',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='description_uz',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='statement_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='statement_ru',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='statement_uz',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='title_en',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='title_ru',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='lessontask',
            name='title_uz',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='title_en',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='title_ru',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='title_uz',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
