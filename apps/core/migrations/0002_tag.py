# NOTE: This is a genuinely NEW table (core_tag did not exist before) —
# applies normally in production, unlike 0001_initial which is --fake-only.

import apps.core.utils
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
            ],
            options={
                'verbose_name': 'Teg',
                'verbose_name_plural': 'Teglar',
                'db_table': 'core_tag',
                'ordering': ['name'],
            },
            bases=(models.Model, apps.core.utils.SlugMixin),
        ),
    ]
