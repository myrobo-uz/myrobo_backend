"""UserCoursePurchase/UserSubscription qanday yaratilishidan qat'iy nazar
(foydalanuvchining o'zi sotib olishi, admin panelda qo'lda qo'shish, yoki
Django admin orqali) Telegram taklif havolalarini yuborishni ta'minlaydi.
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserCoursePurchase, UserSubscription


@receiver(post_save, sender=UserCoursePurchase)
def send_invite_links_on_course_purchase(sender, instance, created, **kwargs):
    if not created or not instance.user.telegram_id:
        return

    from .tasks import send_course_invite_links_task

    telegram_id = instance.user.telegram_id
    course_id = str(instance.course_id)
    transaction.on_commit(
        lambda: send_course_invite_links_task.delay(telegram_id=telegram_id, course_id=course_id)
    )


@receiver(post_save, sender=UserSubscription)
def send_invite_links_on_subscription(sender, instance, created, **kwargs):
    if not created or not instance.user.telegram_id:
        return

    from .tasks import send_subscription_invite_links_task

    telegram_id = instance.user.telegram_id
    plan_id = str(instance.plan_id)
    transaction.on_commit(
        lambda: send_subscription_invite_links_task.delay(telegram_id=telegram_id, plan_id=plan_id)
    )
