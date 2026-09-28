from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

from .activity import log_activity
from .models import ActivityType, ExitReason, PageExit, UserActivity


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


class ActionTrackingAPITests(APITestCase):
    """Anonim va login qilgan foydalanuvchilar uchun action/page-exit tracking API testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        token = RefreshToken.for_user(self.user)
        self.auth_header = f"Bearer {token.access_token}"

    # 1. Login qilgan user action yuboradi
    def test_authenticated_user_action_is_recorded(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.post(
            "/api/analytics/action/",
            {"action": "course_view", "page": "course_detail", "path": "/courses/15"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        activity = UserActivity.objects.get(id=response.data["id"])
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.anonymous_id, "")
        self.assertEqual(activity.action, "course_view")
        self.assertEqual(activity.path, "/courses/15")

    # 2. Login qilmagan user action yuboradi
    def test_anonymous_user_action_is_recorded(self):
        response = self.client.post(
            "/api/analytics/action/",
            {"anonymous_id": "anon-123", "action": "course_view", "page": "courses", "path": "/courses"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        activity = UserActivity.objects.get(id=response.data["id"])
        self.assertIsNone(activity.user)
        self.assertEqual(activity.anonymous_id, "anon-123")

    def test_anonymous_action_without_anonymous_id_is_rejected(self):
        response = self.client.post(
            "/api/analytics/action/", {"action": "course_view"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("anonymous_id", response.data)
        self.assertEqual(UserActivity.objects.count(), 0)

    # 3. Anonymous user page-exit yuboradi
    def test_anonymous_page_exit_is_recorded(self):
        response = self.client.post(
            "/api/analytics/page-exit/",
            {
                "anonymous_id": "anon-abc",
                "page": "courses",
                "path": "/courses",
                "exit_reason": "navigation",
                "time_spent": 145,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        exit_log = PageExit.objects.get(id=response.data["id"])
        self.assertIsNone(exit_log.user)
        self.assertEqual(exit_log.anonymous_id, "anon-abc")
        self.assertEqual(exit_log.exit_reason, ExitReason.NAVIGATION)

    # 4. Login qilgan user page-exit yuboradi
    def test_authenticated_page_exit_is_recorded(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.post(
            "/api/analytics/page-exit/",
            {"page": "profile", "path": "/profile", "exit_reason": "logout", "time_spent": 30},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        exit_log = PageExit.objects.get(id=response.data["id"])
        self.assertEqual(exit_log.user, self.user)
        self.assertEqual(exit_log.anonymous_id, "")

    # 5. IP avtomatik aniqlanadi (klient yuborgan qiymatga ishonilmaydi)
    def test_ip_is_detected_by_backend_not_client_payload(self):
        response = self.client.post(
            "/api/analytics/action/",
            {"anonymous_id": "anon-ip", "action": "course_view", "ip_address": "9.9.9.9"},
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1",
        )
        self.assertEqual(response.status_code, 201)
        activity = UserActivity.objects.get(id=response.data["id"])
        self.assertEqual(activity.ip, "203.0.113.5")
        self.assertNotEqual(activity.ip, "9.9.9.9")

    # 6. created_at avtomatik yoziladi
    def test_created_at_is_server_generated(self):
        before = timezone.now()
        response = self.client.post(
            "/api/analytics/action/",
            {
                "anonymous_id": "anon-time",
                "action": "course_view",
                "created_at": "2000-01-01T00:00:00Z",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        activity = UserActivity.objects.get(id=response.data["id"])
        self.assertGreaterEqual(activity.created_at, before)

    # 7. time_spent to'g'ri saqlanadi
    def test_time_spent_is_saved_correctly(self):
        response = self.client.post(
            "/api/analytics/page-exit/",
            {"anonymous_id": "anon-t2", "page": "cart", "time_spent": 77},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PageExit.objects.get(id=response.data["id"]).time_spent, 77)

    # 8. Noto'g'ri request validationdan o'tmaydi
    def test_invalid_page_exit_negative_time_spent_is_rejected(self):
        response = self.client.post(
            "/api/analytics/page-exit/",
            {"anonymous_id": "anon-neg", "page": "cart", "time_spent": -5},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_page_exit_missing_page_is_rejected(self):
        response = self.client.post(
            "/api/analytics/page-exit/", {"anonymous_id": "anon-nopage"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    # 9. Mavjud (login qilgan foydalanuvchilar uchun) action functionality buzilmaganligi
    def test_existing_log_activity_helper_still_works_for_authenticated_user(self):
        log_activity(self.user, ActivityType.LOGIN, description="login")
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.user, action=ActivityType.LOGIN, anonymous_id=""
            ).exists()
        )
