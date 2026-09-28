from .models import ActivityType, UserActivity
from .utils import get_client_ip


def log_activity(
    user,
    action,
    request=None,
    description="",
    target=None,
    meta=None,
    anonymous_id="",
    page="",
    path="",
):
    """Foydalanuvchi (yoki anonim tashrifchi) amalini UserActivity jadvaliga yozadi.

    `user` login qilmagan bo'lsa (None yoki is_authenticated=False), yozuv
    `anonymous_id` bilan saqlanadi — bu holatda `anonymous_id` bo'sh bo'lmasligi kerak.

    Kutilmagan xatolik (masalan, DB band) so'rovni to'xtatmasligi uchun
    xatolar yutiladi — presence.touch_online bilan bir xil naqsh.
    """
    try:
        is_authenticated = bool(user and getattr(user, "is_authenticated", False))
        if not is_authenticated:
            if not anonymous_id:
                return
            user = None
        UserActivity.objects.create(
            user=user,
            anonymous_id=anonymous_id if not is_authenticated else "",
            action=action,
            description=description,
            page=page,
            path=path,
            target_type=target.__class__.__name__.lower() if target is not None else "",
            target_id=str(getattr(target, "id", "")) if target is not None else "",
            meta=meta or {},
            ip=get_client_ip(request) if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        )
    except Exception:
        pass


__all__ = ["ActivityType", "log_activity"]
