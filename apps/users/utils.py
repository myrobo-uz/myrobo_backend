import json
import secrets

from django_redis import get_redis_connection

OTP_TTL = 180


def generate_code() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def save_otp(telegram_id, extra_data=None):
    code = generate_code()
    payload = {"telegram_id": str(telegram_id)}
    if extra_data:
        payload.update(extra_data)
    get_redis_connection("default").setex(f"otp:{code}", OTP_TTL, json.dumps(payload))
    return code


def verify_otp(code):
    if not code:
        return "invalid"
    redis_conn = get_redis_connection("default")
    key = f"otp:{code}"
    raw = redis_conn.get(key)
    if not raw:
        return "invalid"
    redis_conn.delete(key)
    return json.loads(raw)
