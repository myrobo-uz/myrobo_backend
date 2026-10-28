from django.conf import settings


def set_refresh_cookie(response, refresh_token: str):
    """Refresh tokenni umumiy (parent-domain) httponly cookie sifatida qo'yadi.

    Bu boshqa frontend (masalan market.myrobo.uz) bir xil cookie orqali
    /user/token/refresh/ ni chaqirib, qayta login qilmasdan yangi access
    token olishiga imkon beradi (SSO).
    """
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        domain=settings.SSO_COOKIE_DOMAIN,
        path="/",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="Lax",
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.SSO_COOKIE_DOMAIN,
        path="/",
        samesite="Lax",
    )
