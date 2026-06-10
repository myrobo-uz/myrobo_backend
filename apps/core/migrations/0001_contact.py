import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Contact",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("name", models.CharField(max_length=256, verbose_name="Ism")),
                ("email", models.EmailField(verbose_name="Email")),
                ("message", models.TextField(verbose_name="Xabar")),
                ("image", models.ImageField(blank=True, null=True, upload_to="contacts/images/", verbose_name="Rasm")),
            ],
            options={
                "verbose_name": "Murojaat",
                "verbose_name_plural": "Murojaatlar",
                "db_table": "core_contact",
                "ordering": ["-created_at"],
            },
        ),
    ]
