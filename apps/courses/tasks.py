from celery import shared_task
from django.db.models import Prefetch
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def expire_subscriptions_task(self):
    from .models import (
        CourseTelegramLink,
        UserCoursePurchase,
        UserSubscription,
    )
    from .telegram_service import kick_user_from_course_chats

    now = timezone.now()

    expired_subs = (
        UserSubscription.objects.filter(is_active=True, expires_at__lte=now)
        .select_related("user", "plan")
        .prefetch_related(
            Prefetch(
                "plan__courses__telegram_links",
                queryset=CourseTelegramLink.objects.filter(is_active=True),
            )
        )
    )

    sub_ids = list(expired_subs.values_list("id", flat=True))
    total = len(sub_ids)

    kicked_users = 0
    errors = 0

    for sub in expired_subs.iterator(chunk_size=200):
        try:
            user = sub.user
            telegram_id = user.telegram_id
            plan_courses = list(sub.plan.courses.all())

            if not telegram_id:
                continue

            course_ids = [c.id for c in plan_courses]
            individual_ids = set(
                UserCoursePurchase.objects.filter(user=user, course_id__in=course_ids)
                .values_list("course_id", flat=True)
            )
            other_sub_courses = set(
                UserSubscription.objects.filter(
                    user=user,
                    is_active=True,
                    expires_at__gt=now,
                    plan__courses__id__in=course_ids,
                )
                .exclude(id=sub.id)
                .values_list("plan__courses__id", flat=True)
            )

            for plan_course in plan_courses:
                telegram_links = list(plan_course.telegram_links.all())
                if not telegram_links:
                    continue
                if plan_course.id in individual_ids:
                    continue
                if plan_course.id in other_sub_courses:
                    continue
                kick_user_from_course_chats(telegram_id, telegram_links)

            kicked_users += 1
        except Exception:
            errors += 1

    if sub_ids:
        UserSubscription.objects.filter(id__in=sub_ids).update(is_active=False)

    # Market tomonidan yoziladigan CourseSubscription uchun ham xuddi shunday:
    # muddati tugaganlarni yopamiz, lekin foydalanuvchida shu kursga boshqa
    # kirish huquqi (purchase, plan yoki boshqa faol CourseSubscription) qolgan
    # bo'lsa, chatdan chiqarib yubormaymiz.
    from .models import CourseSubscription

    expired_course_subs = list(
        CourseSubscription.objects.filter(is_active=True, expires_at__lte=now)
        .select_related("user", "course")
    )
    cs_ids = [cs.id for cs in expired_course_subs]
    if cs_ids:
        CourseSubscription.objects.filter(id__in=cs_ids).update(is_active=False)

    cs_kicked = 0
    cs_errors = 0
    for cs in expired_course_subs:
        try:
            telegram_id = cs.user.telegram_id
            if not telegram_id:
                continue
            telegram_links = list(
                CourseTelegramLink.objects.filter(course=cs.course, is_active=True)
            )
            if not telegram_links:
                continue
            if cs.course.user_has_access(cs.user):
                continue
            kick_user_from_course_chats(telegram_id, telegram_links)
            cs_kicked += 1
        except Exception:
            cs_errors += 1

    return {
        "processed": total,
        "kicked": kicked_users,
        "errors": errors,
        "course_subscriptions_processed": len(cs_ids),
        "course_subscriptions_kicked": cs_kicked,
        "course_subscriptions_errors": cs_errors,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def send_course_invite_links_task(self, telegram_id: int, course_id: str):
    from .models import CourseTelegramLink
    from .telegram_service import send_invite_links_to_user

    try:
        telegram_links = list(
            CourseTelegramLink.objects.filter(course_id=course_id, is_active=True)
        )
        if telegram_links:
            send_invite_links_to_user(telegram_id, telegram_links)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def send_pending_course_subscription_invites_task(self):
    """Market CourseSubscription yaratganda Celery'ga to'g'ridan-to'g'ri murojaat
    qila olmaydi, shuning uchun bu vazifa har daqiqada hali taklif havolasi
    yuborilmagan (invite_sent_at bo'sh) faol obunalarni topib, mavjud
    send_course_invite_links_task orqali yuboradi.
    """
    from .models import CourseSubscription

    now = timezone.now()
    pending = list(
        CourseSubscription.objects.filter(
            is_active=True, expires_at__gt=now, invite_sent_at__isnull=True,
        ).select_related("user", "course")
    )

    sent = 0
    for cs in pending:
        CourseSubscription.objects.filter(id=cs.id).update(invite_sent_at=now)
        if cs.user.telegram_id:
            send_course_invite_links_task.delay(
                telegram_id=cs.user.telegram_id, course_id=str(cs.course_id)
            )
            sent += 1

    return {"processed": len(pending), "sent": sent}


@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def send_course_resources_task(self, telegram_id: int, course_id: str):
    from .models import CourseResource
    from .telegram_service import send_course_resources_to_user

    try:
        resources = list(
            CourseResource.objects.filter(course_id=course_id).order_by("order", "created_at")
        )
        if resources:
            send_course_resources_to_user(telegram_id, resources)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def send_subscription_invite_links_task(self, telegram_id: int, plan_id: str):
    from .models import CoursePlan, CourseTelegramLink
    from .telegram_service import send_invite_links_to_user

    try:
        plan = CoursePlan.objects.prefetch_related(
            Prefetch(
                "courses__telegram_links",
                queryset=CourseTelegramLink.objects.filter(is_active=True),
            )
        ).get(id=plan_id)

        all_links = [link for course in plan.courses.all() for link in course.telegram_links.all()]
        if all_links:
            send_invite_links_to_user(telegram_id, all_links)
    except Exception as exc:
        raise self.retry(exc=exc)
