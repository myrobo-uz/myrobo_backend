import time

from django_redis import get_redis_connection

ONLINE_KEY = "analytics:online_users"
ONLINE_WINDOW_SECONDS = 300


def touch_online(user_id) -> None:
    try:
        conn = get_redis_connection("default")
        conn.zadd(ONLINE_KEY, {str(user_id): time.time()})
    except Exception:
        pass


def _trim(conn, window: int) -> None:
    conn.zremrangebyscore(ONLINE_KEY, "-inf", time.time() - window)


def get_online_count(window: int = ONLINE_WINDOW_SECONDS) -> int:
    try:
        conn = get_redis_connection("default")
        _trim(conn, window)
        return conn.zcard(ONLINE_KEY)
    except Exception:
        return 0


def get_online_user_ids(window: int = ONLINE_WINDOW_SECONDS) -> list:
    try:
        conn = get_redis_connection("default")
        _trim(conn, window)
        return [uid.decode() if isinstance(uid, bytes) else uid for uid in conn.zrange(ONLINE_KEY, 0, -1)]
    except Exception:
        return []
