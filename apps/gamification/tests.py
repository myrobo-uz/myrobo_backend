from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course, Lesson, Module
from apps.users.models import User

from .models import Certificate, Rank, XPLog, XPReason
from .utils import (
    award_xp,
    get_current_rank,
    get_leaderboard_position,
    get_next_rank,
    issue_certificate_if_course_completed,
)


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


def _make_course(title="Python asoslari"):
    img = SimpleUploadedFile("course.jpg", b"filecontent", content_type="image/jpeg")
    return Course.objects.create(title=title, price=0, image=img)


class XPUtilsTests(APITestCase):
    def setUp(self):
        self.user = _make_user()

    def test_award_xp_creates_log_and_increments_user_xp(self):
        award_xp(self.user, amount=15, reason=XPReason.LESSON_COMPLETE, description="1-dars")
        self.user.refresh_from_db()
        self.assertEqual(self.user.xp, 15)
        self.assertEqual(XPLog.objects.filter(user=self.user).count(), 1)

    def test_award_xp_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError):
            award_xp(self.user, amount=0, reason=XPReason.OTHER)

    def test_current_and_next_rank_are_computed_from_xp(self):
        Rank.objects.create(title="Boshlovchi", min_xp=0)
        intermediate = Rank.objects.create(title="O'rta", min_xp=100)
        expert = Rank.objects.create(title="Ekspert", min_xp=500)

        award_xp(self.user, amount=150, reason=XPReason.MANUAL)
        self.user.refresh_from_db()

        self.assertEqual(get_current_rank(self.user), intermediate)
        self.assertEqual(get_next_rank(self.user), expert)

    def test_leaderboard_position_reflects_xp_ranking(self):
        other = _make_user(telegram_id=2, phone="+998900000002", full_name="Other User")
        award_xp(self.user, amount=50, reason=XPReason.MANUAL)
        award_xp(other, amount=200, reason=XPReason.MANUAL)
        self.user.refresh_from_db()
        other.refresh_from_db()

        self.assertEqual(get_leaderboard_position(other), 1)
        self.assertEqual(get_leaderboard_position(self.user), 2)

    def test_certificate_issued_only_once_when_course_fully_completed(self):
        course = _make_course()
        module = Module.objects.create(course=course, title="1-modul")
        Lesson.objects.create(module=module, lesson_type="content", title="Dars 1")

        from apps.courses.models import LessonProgress

        lesson = module.lessons.first()
        LessonProgress.objects.create(user=self.user, lesson=lesson, is_completed=True)

        cert1 = issue_certificate_if_course_completed(self.user, course)
        cert2 = issue_certificate_if_course_completed(self.user, course)

        self.assertIsNotNone(cert1)
        self.assertEqual(cert1.id, cert2.id)
        self.assertEqual(Certificate.objects.filter(user=self.user, course=course).count(), 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.xp, 100)


class GamificationAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_ranks_list_is_public(self):
        Rank.objects.create(title="Boshlovchi", min_xp=0)
        client = APIClient()
        response = client.get("/gamification/ranks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_my_xp_requires_authentication(self):
        client = APIClient()
        response = client.get("/gamification/my-xp/")
        self.assertEqual(response.status_code, 401)

    def test_my_xp_returns_current_state(self):
        Rank.objects.create(title="Boshlovchi", min_xp=0)
        award_xp(self.user, amount=10, reason=XPReason.MANUAL)
        response = self.client.get("/gamification/my-xp/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["xp"], 10)
        self.assertEqual(response.data["rank"]["title"], "Boshlovchi")

    def test_profile_stats_counts_certificates(self):
        course = _make_course()
        module = Module.objects.create(course=course, title="1-modul")
        Lesson.objects.create(module=module, lesson_type="content", title="Dars 1")
        from apps.courses.models import LessonProgress
        LessonProgress.objects.create(user=self.user, lesson=module.lessons.first(), is_completed=True)
        issue_certificate_if_course_completed(self.user, course)

        response = self.client.get("/gamification/profile-stats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_certificates"], 1)
        self.assertEqual(response.data["total_courses_completed"], 1)

    def test_leaderboard_is_public_and_ordered_by_xp(self):
        other = _make_user(telegram_id=2, phone="+998900000002", full_name="Other User")
        award_xp(self.user, amount=30, reason=XPReason.MANUAL)
        award_xp(other, amount=90, reason=XPReason.MANUAL)

        client = APIClient()
        response = client.get("/gamification/leaderboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["full_name"], "Other User")
        self.assertEqual(response.data[0]["xp"], 90)
