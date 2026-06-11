from django.core.cache import cache
from rest_framework.exceptions import Throttled
from rest_framework.throttling import BaseThrottle


class IPRateThrottle(BaseThrottle):
    RATE = 50
    WINDOW = 1
    MAX_VIOLATIONS = 2
    VIOLATION_TTL = 3600

    def get_ident(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def allow_request(self, request, view):
        ip = self.get_ident(request)
        count_key = f"throttle:count:{ip}"
        violation_key = f"throttle:violations:{ip}"

        violations = cache.get(violation_key, 0)
        count = cache.get(count_key, 0)

        if violations > self.MAX_VIOLATIONS:
            raise Throttled(detail="Bloklandi: IP manzil vaqtincha bloklangan.")

        if count >= self.RATE:
            new_v = violations + 1
            cache.set(violation_key, new_v, self.VIOLATION_TTL)
            if new_v > self.MAX_VIOLATIONS:
                raise Throttled(detail="Bloklandi: IP manzil vaqtincha bloklangan.")
            raise Throttled(
                detail=f"Ogohlantirish {new_v}/{self.MAX_VIOLATIONS}: so'rovlar juda tez kelmoqda."
            )

        if count == 0:
            cache.set(count_key, 1, self.WINDOW)
        else:
            try:
                cache.incr(count_key)
            except Exception:
                cache.set(count_key, count + 1, self.WINDOW)
        return True

    def wait(self):
        return self.WINDOW
