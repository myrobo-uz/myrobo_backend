from django.db.models import Count, Q

from .models import LessonProgress


def get_course_progress(user, course):
    totals = course.modules.aggregate(total=Count("lessons"))
    total = totals.get("total") or 0
    if total == 0:
        return 0

    completed = LessonProgress.objects.filter(
        user=user,
        is_completed=True,
        lesson__module__course=course,
    ).count()
    return round((completed / total) * 100, 2)


def apply_promo(price, promo):
    if not promo or not promo.is_valid():
        return price
    discount = (price * promo.discount_percent) / 100
    return price - discount


