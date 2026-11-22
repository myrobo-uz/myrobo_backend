# NOTE: v0.0.43'da bu maydonlar (allowed_users, is_public + index) avvalgi
# nomdagi migratsiya ('0009_courseresource_...') orqali productionda
# ALLAQACHON qo'llangan. Bu fayl keyinroq CourseResource modeli olib
# tashlanib qayta generatsiya qilinganda nom o'zgargani uchun, Django uni
# "yangi" deb hisoblaydi. Shuning uchun productionda --fake bilan
# qo'llanadi (hech narsa o'zgartirmaydi); resource_code haqiqiy ustuni
# 0010-migratsiyada REAL qo'shiladi.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_tag'),
        ('courses', '0008_coursesubscription_invite_sent_at'),
        ('users', '0002_user_xp'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='allowed_users',
            field=models.ManyToManyField(blank=True, help_text="is_public=False bo'lganda shu kursni ko'ra oladigan foydalanuvchilar", related_name='visible_courses', to='users.user'),
        ),
        migrations.AddField(
            model_name='course',
            name='is_public',
            field=models.BooleanField(default=True, help_text="True bo'lsa barcha foydalanuvchiga ko'rinadi, False bo'lsa faqat allowed_users'ga"),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['is_public'], name='courses_cou_is_publ_bfb162_idx'),
        ),
    ]
