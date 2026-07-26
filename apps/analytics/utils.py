from django.db.models.functions import TruncDate, TruncMonth, TruncYear

PERIOD_TRUNC = {
    "daily": TruncDate,
    "monthly": TruncMonth,
    "yearly": TruncYear,
}


def get_client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def apply_period_trunc(qs, period: str, field: str):
    trunc_fn = PERIOD_TRUNC.get(period, TruncDate)
    return (
        qs.annotate(period=trunc_fn(field))
        .values("period")
        .order_by("period")
    )


def course_progress_for_users(course, user_ids: list) -> dict:
    """
    Returns {user_id: {"completed_lessons": int, "total_lessons": int, "percent": float}}
    for the given course, batched into 2 extra queries regardless of len(user_ids).
    """
    from django.db.models import Count

    from apps.courses.models import Course, LessonProgress

    if not user_ids:
        return {}

    total_lessons = Course.objects.filter(id=course.id).annotate(
        total=Count("modules__lessons")
    ).values_list("total", flat=True).first() or 0

    progress_rows = (
        LessonProgress.objects
        .filter(user_id__in=user_ids, lesson__module__course_id=course.id, is_completed=True)
        .values("user_id")
        .annotate(completed=Count("id"))
    )
    completed_map = {row["user_id"]: row["completed"] for row in progress_rows}

    result = {}
    for user_id in user_ids:
        completed = completed_map.get(user_id, 0)
        percent = round((completed / total_lessons) * 100, 2) if total_lessons > 0 else 0.0
        result[user_id] = {
            "completed_lessons": completed,
            "total_lessons": total_lessons,
            "percent": percent,
        }
    return result
