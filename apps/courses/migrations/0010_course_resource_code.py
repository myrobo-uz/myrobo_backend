# resource_code — 0009'dan ajratilgan, chunki 0009 productionda --fake bilan
# qo'llanadi (uning boshqa maydonlari allaqachon mavjud). Bu esa yagona
# haqiqatan ham YANGI ustun, shuning uchun REAL (--fake'siz) qo'llanishi kerak.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_course_allowed_users_course_is_public_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='resource_code',
            field=models.CharField(blank=True, default='', help_text='Resurs boti (kino_bot)dagi kod — masalan 701. /start <code> deep-link uchun ishlatiladi.', max_length=32),
        ),
    ]
