# NOTE: This is the only genuinely NEW schema change for articles — applies
# normally in production, unlike 0001_initial which is --fake-only.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_tag'),
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='articles',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='articles', to='core.tag'),
        ),
    ]
