import base64
from django.conf import settings


def payme_checkout_link(order_id, amount_tiyin: int, lang: str = "uz", callback_url: str = None) -> str:
    params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount_tiyin};l={lang}"
    if callback_url:
        params += f";c={callback_url}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"



