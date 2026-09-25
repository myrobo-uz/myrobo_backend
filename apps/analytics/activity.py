from .models import ActivityType, UserActivity
from .utils import get_client_ip


def log_activity(user, action, request=None, description="", target=None, meta=None):
    """Foydalanuvchi amalini UserActivity jadvaliga yozadi.

    Kutilmagan xatolik (masalan, DB band) so'rovni to'xtatmasligi uchun
    xatolar yutiladi — presence.touch_online bilan bir xil naqsh.
    """
    try:
        if not user or not getattr(user, "is_authenticated", False):
            return
        UserActivity.objects.create(
            user=user,
            action=action,
            description=description,
            target_type=target.__class__.__name__.lower() if target is not None else "",
            target_id=str(getattr(target, "id", "")) if target is not None else "",
            meta=meta or {},
            ip=get_client_ip(request) if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        )
    except Exception:
        pass


__all__ = ["ActivityType", "log_activity"]
