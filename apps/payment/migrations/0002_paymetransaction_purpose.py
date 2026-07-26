from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymetransaction',
            name='purpose',
            field=models.CharField(
                blank=True,
                choices=[('topup', "Balans to'ldirish"), ('donate', 'Donate')],
                db_index=True,
                default='topup',
                max_length=10,
            ),
        ),
    ]
