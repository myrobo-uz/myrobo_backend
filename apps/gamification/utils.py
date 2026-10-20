from django.db.models import F

from apps.users.models import User

from .models import Certificate, Rank, XPLog, XPReason


def award_xp(user, amount: int, reason: str, description: str = "", target=None) -> XPLog:
    """Foydalanuvchiga XP beradi: XPLog yozuvi yaratadi va User.xp ni atomik oshiradi."""
    if amount <= 0:
        raise ValueError("amount musbat bo'lishi kerak")

    log = XPLog.objects.create(
        user=user,
        amount=amount,
        reason=reason,
        description=description,
        target_type=target.__class__.__name__.lower() if target is not None else "",
        target_id=str(getattr(target, "id", "")) if target is not None else "",
    )
    User.objects.filter(id=user.id).update(xp=F("xp") + amount)
    user.xp = (user.xp or 0) + amount
    return log


def get_current_rank(user) -> Rank | None:
    return Rank.objects.filter(min_xp__lte=user.xp).order_by("-min_xp").first()


def get_next_rank(user) -> Rank | None:
    return Rank.objects.filter(min_xp__gt=user.xp).order_by("min_xp").first()


def get_leaderboard_position(user) -> int:
    return User.objects.filter(xp__gt=user.xp).count() + 1


def issue_certificate_if_course_completed(user, course) -> Certificate | None:
    """Kurs 100% tugatilgan bo'lsa sertifikat beradi (bir marta) va XP mukofotlaydi."""
    from apps.courses.utils import get_course_progress

    if get_course_progress(user, course) < 100:
        return None

    certificate, created = Certificate.objects.get_or_create(user=user, course=course)
    if created:
        award_xp(
            user, amount=100, reason=XPReason.COURSE_COMPLETE,
            description=course.title, target=course,
        )
    return certificate
