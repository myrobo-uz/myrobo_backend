import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("name", models.CharField(max_length=255, unique=True, verbose_name="Korxona nomi")),
                ("description", models.TextField(blank=True, default="", verbose_name="Tavsif")),
            ],
            options={
                "verbose_name": "Korxona",
                "verbose_name_plural": "Korxonalar",
                "db_table": "courses_company",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="promocode",
            name="company",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="promocodes",
                to="courses.company",
                verbose_name="Korxona",
            ),
        ),
    ]
