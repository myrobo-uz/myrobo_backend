# NOTE: This is the only genuinely NEW schema change here — applies normally
# in production, unlike 0003_translations_backfill which is --fake-only.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_tag'),
        ('courses', '0003_translations_backfill'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='course',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='courses', to='core.tag'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['is_archived'], name='courses_cou_is_arch_fc08ef_idx'),
        ),
    ]
