from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0005_alter_lesson_lesson_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="old_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
            ),
        ),
    ]
