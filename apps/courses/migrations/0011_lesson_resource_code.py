# resource_code kurs darajasidan dars (Lesson) darajasiga ko'chirildi —
# har bir dars uchun alohida resurs kodi bo'lishi kerak, butun kurs uchun emas.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_course_resource_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='resource_code',
        ),
        migrations.AddField(
            model_name='lesson',
            name='resource_code',
            field=models.CharField(blank=True, default='', help_text='Resurs boti (kino_bot)dagi kod — masalan 701. /start <code> deep-link uchun ishlatiladi.', max_length=32),
        ),
    ]
