from django.db import models
from apps.users.models import User


class PaymeTransaction(models.Model):
    PROVIDER_PAYME = "payme"
    PROVIDER_CHOICES = ((PROVIDER_PAYME, "Payme"),)

    STATE_PENDING = 1
    STATE_DONE = 2
    STATE_CANCELED = -1
    STATE_CHOICES = (
        (STATE_PENDING, "Pending"),
        (STATE_DONE, "Done"),
        (STATE_CANCELED, "Canceled"),
    )

    PURPOSE_TOPUP = "topup"
    PURPOSE_DONATE = "donate"
    PURPOSE_CHOICES = (
        (PURPOSE_TOPUP, "Balans to'ldirish"),
        (PURPOSE_DONATE, "Donate"),
    )

    id = models.BigAutoField(primary_key=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_PAYME)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default=PURPOSE_TOPUP, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payme_transactions")
    payme_transaction_id = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    amount_tiyin = models.PositiveBigIntegerField()
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=STATE_PENDING, db_index=True)
    create_time = models.BigIntegerField(default=0)
    perform_time = models.BigIntegerField(null=True, blank=True)
    cancel_time = models.BigIntegerField(null=True, blank=True)
    reason = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "backend_payme_transaction"
        ordering = ("-created_at",)

    def __str__(self):
        return f"PaymeTransaction #{self.id} | user={self.user_id} | {self.amount_tiyin/100:.2f} som | {self.get_state_display()}"

    def amount_som(self):
        return self.amount_tiyin / 100
