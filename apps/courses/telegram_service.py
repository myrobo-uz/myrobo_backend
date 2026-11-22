import logging
import os

import requests
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_BOT_USERNAME_CACHE_KEY = "myrobo_bot_username"

BACKEND_BOT_TOKEN_C = os.environ.get("TELEGRAM_BOT_TOKEN_CONTACT", "")
BACKEND_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BACKEND_BOT_TOKEN}"
TELEGRAM_API_C = f"https://api.telegram.org/bot{BACKEND_BOT_TOKEN_C}"

_session = requests.Session()
_retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504),
    allowed_methods=("POST",),
)
_session.mount("https://", HTTPAdapter(max_retries=_retry, pool_connections=20, pool_maxsize=50))


def _bot_request(method: str, **kwargs):
    if not BACKEND_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN sozlanmagan, %s chaqiruvi o'tkazib yuborildi", method)
        return None
    try:
        resp = _session.post(f"{TELEGRAM_API}/{method}", json=kwargs, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            logger.warning(
                "Telegram API %s muvaffaqiyatsiz: %s (params=%s)",
                method, data.get("description"), kwargs,
            )
            return None
        return data.get("result")
    except Exception:
        logger.exception("Telegram API %s so'rovi xato bilan tugadi (params=%s)", method, kwargs)
        return None


def create_invite_link(chat_id: int, member_limit: int = 1):
    result = _bot_request(
        "createChatInviteLink",
        chat_id=chat_id,
        member_limit=member_limit,
        creates_join_request=False,
    )
    return result.get("invite_link") if result else None


def revoke_invite_link(chat_id: int, invite_link: str) -> bool:
    result = _bot_request("revokeChatInviteLink", chat_id=chat_id, invite_link=invite_link)
    return result is not None


def kick_user_from_chat(chat_id: int, telegram_id: int) -> bool:
    banned = _bot_request(
        "banChatMember", chat_id=chat_id, user_id=telegram_id, revoke_messages=False
    )
    if not banned:
        return False
    _bot_request("unbanChatMember", chat_id=chat_id, user_id=telegram_id, only_if_banned=True)
    return True


def send_invite_links_to_user(telegram_id: int, course_telegram_links) -> bool:
    if not course_telegram_links:
        return True

    lines = ["🎓 <b>Kurs guruhlariga qo'shilish havolalari:</b>\n"]
    success_count = 0

    for tg_link in course_telegram_links:
        if not tg_link.is_active:
            continue
        invite_link = create_invite_link(tg_link.chat_id, member_limit=1)
        if invite_link:
            lines.append(f"📌 <b>{tg_link.title}</b>\n🔗 {invite_link}")
            success_count += 1

    if success_count == 0:
        return False

    lines.append("\n⚠️ <i>Havolalar bir martalik — faqat siz uchun.</i>")
    result = _bot_request(
        "sendMessage", chat_id=telegram_id, text="\n".join(lines), parse_mode="HTML"
    )
    return result is not None


def get_bot_username() -> str | None:
    cached = cache.get(_BOT_USERNAME_CACHE_KEY)
    if cached:
        return cached
    result = _bot_request("getMe")
    username = result.get("username") if result else None
    if username:
        cache.set(_BOT_USERNAME_CACHE_KEY, username, timeout=60 * 60 * 24)
    return username


def get_bot_deep_link() -> str | None:
    username = get_bot_username()
    return f"https://t.me/{username}" if username else None


def copy_message(chat_id: int, from_chat_id: int, message_id: int, caption: str | None = None) -> bool:
    kwargs = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    if caption:
        kwargs["caption"] = caption
        kwargs["parse_mode"] = "HTML"
    return _bot_request("copyMessage", **kwargs) is not None


def send_course_resources_to_user(telegram_id: int, course_resources) -> bool:
    if not course_resources:
        return False

    success_count = 0
    for resource in course_resources:
        if copy_message(telegram_id, resource.channel_id, resource.message_id, caption=resource.title or None):
            success_count += 1

    return success_count > 0


def kick_user_from_course_chats(telegram_id: int, course_telegram_links) -> None:
    for tg_link in course_telegram_links:
        if not tg_link.is_active:
            continue
        kick_user_from_chat(tg_link.chat_id, telegram_id)


def send_contact_to_group(chat_id: int | str, name: str, email: str, message: str, image_bytes: bytes | None = None) -> bool:
    text = (
        f"📩 <b>Yangi murojaat</b>\n\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📧 <b>Email:</b> {email}\n"
        f"💬 <b>Xabar:</b>\n{message}"
    )
    if image_bytes:
        try:
            resp = _session.post(
                f"{TELEGRAM_API_C}/sendPhoto",
                data={"chat_id": chat_id, "caption": text, "parse_mode": "HTML"},
                files={"photo": ("image.jpg", image_bytes, "image/jpeg")},
                timeout=15,
            )
            data = resp.json()
            return bool(data.get("ok") and data.get("result"))
        except Exception:
            return False

    result = _bot_request("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")
    return result is not None
