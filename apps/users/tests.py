from unittest.mock import patch

from django.conf import settings
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


class SSOCookieTests(APITestCase):
    """Login/refresh/logout orqali umumiy (parent-domain) SSO cookie ishlashini tekshiradi."""

    def setUp(self):
        self.client = APIClient()

    def _login(self, telegram_id=555, phone_number="+998901112233", full_name="SSO Test"):
        with patch("apps.users.views.verify_otp") as mocked_verify:
            mocked_verify.return_value = {
                "telegram_id": str(telegram_id),
                "full_name": full_name,
                "phone_number": phone_number,
            }
            return self.client.post("/user/login/", {"code": "123456"}, format="json")

    # 1. Login refresh tokenni ham javob tanasida, ham cookie'da qaytaradi
    def test_login_sets_refresh_cookie(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.REFRESH_COOKIE_NAME, response.cookies)
        cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
        self.assertEqual(cookie.value, response.data["refresh"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["path"], "/")

    # 2. Cookie orqali (body'da refresh bo'lmasa ham) yangi access token olish mumkin — SSO'ning asosi
    def test_refresh_works_from_cookie_without_body(self):
        login_response = self._login()
        self.assertEqual(login_response.status_code, 200)
        # Django test client keyingi so'rovlarga cookie'larni avtomatik qo'shadi (brauzerni taqlid qiladi)
        refresh_response = self.client.post("/user/token/refresh/", {}, format="json")
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)

    # 3. Eski frontend uchun orqaga moslik — body'da refresh yuborilsa ham ishlaydi
    def test_refresh_still_works_with_explicit_body(self):
        user = _make_user()
        refresh = RefreshToken.for_user(user)
        client = APIClient()  # cookie'siz, toza client
        response = client.post("/user/token/refresh/", {"refresh": str(refresh)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    # 4. Na body'da, na cookie'da refresh bo'lmasa — aniq xato
    def test_refresh_without_token_anywhere_is_rejected(self):
        client = APIClient()
        response = client.post("/user/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    # 5. Logout umumiy cookie'ni tozalaydi
    def test_logout_clears_cookie(self):
        self._login()
        self.assertIn(settings.REFRESH_COOKIE_NAME, self.client.cookies)

        logout_response = self.client.post("/user/logout/")
        self.assertEqual(logout_response.status_code, 200)
        cleared = logout_response.cookies[settings.REFRESH_COOKIE_NAME]
        # Brauzerga o'chirish buyrug'i: bo'sh qiymat + o'tmishdagi muddat
        self.assertEqual(cleared.value, "")

    # 6. Mavjud (eski) login javobi tuzilishi buzilmaganligi
    def test_login_response_shape_is_unchanged(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        for key in ("status", "access", "refresh", "user"):
            self.assertIn(key, response.data)
