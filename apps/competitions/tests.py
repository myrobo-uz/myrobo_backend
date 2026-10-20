from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

from .models import Competition, CompetitionParticipant, ParticipantStatus


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


def _make_competition(title="Robo musobaqa", hours_from=-1, hours_to=1, xp_reward=100):
    now = timezone.now()
    return Competition.objects.create(
        title=title,
        start_date=now + timedelta(hours=hours_from),
        end_date=now + timedelta(hours=hours_to),
        xp_reward=xp_reward,
    )


class CompetitionAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_active_competition_is_listed_with_active_status(self):
        _make_competition(hours_from=-1, hours_to=1)
        client = APIClient()
        response = client.get("/competitions/", {"status": "active"})
        self.assertEqual(response.data["results"][0]["status"], "active")

    def test_finished_competition_excluded_from_active_filter(self):
        _make_competition(title="Eski musobaqa", hours_from=-10, hours_to=-5)
        client = APIClient()
        response = client.get("/competitions/", {"status": "active"})
        self.assertEqual(response.data["count"], 0)

    def test_join_requires_authentication(self):
        competition = _make_competition()
        client = APIClient()
        response = client.post(f"/competitions/{competition.slug}/join/")
        self.assertEqual(response.status_code, 401)

    def test_user_can_join_active_competition_once(self):
        competition = _make_competition()
        response = self.client.post(f"/competitions/{competition.slug}/join/")
        self.assertEqual(response.status_code, 201)

        response2 = self.client.post(f"/competitions/{competition.slug}/join/")
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(CompetitionParticipant.objects.filter(user=self.user).count(), 1)

    def test_cannot_join_finished_competition(self):
        competition = _make_competition(hours_from=-10, hours_to=-5)
        response = self.client.post(f"/competitions/{competition.slug}/join/")
        self.assertEqual(response.status_code, 400)

    def test_detail_shows_is_joined_flag(self):
        competition = _make_competition()
        response = self.client.get(f"/competitions/{competition.slug}/")
        self.assertFalse(response.data["is_joined"])

        self.client.post(f"/competitions/{competition.slug}/join/")
        response = self.client.get(f"/competitions/{competition.slug}/")
        self.assertTrue(response.data["is_joined"])

    def test_my_competitions_lists_joined_only(self):
        competition = _make_competition()
        _make_competition(title="Boshqa musobaqa")
        self.client.post(f"/competitions/{competition.slug}/join/")

        response = self.client.get("/competitions/my/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["competition_title"], "Robo musobaqa")

    def test_direction_filter(self):
        from apps.core.models import Tag

        tag = Tag.objects.create(name="Elektronika")
        c1 = _make_competition(title="Elektronika musobaqasi")
        c1.directions.add(tag)
        _make_competition(title="Dasturlash musobaqasi")

        client = APIClient()
        response = client.get("/competitions/", {"direction": tag.slug})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Elektronika musobaqasi")


class AdminMarkWinnerAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _make_user(telegram_id=99, phone="+998900000099", full_name="Admin")
        self.admin.is_admin = True
        self.admin.save(update_fields=["is_admin"])
        token = RefreshToken.for_user(self.admin).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        self.participant_user = _make_user(telegram_id=2, phone="+998900000002", full_name="Ishtirokchi")
        self.competition = _make_competition(xp_reward=75)
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition, user=self.participant_user,
        )

    def test_mark_winner_awards_xp_once(self):
        response = self.client.post(
            f"/api/admin/competition-participants/{self.participant.id}/mark-winner/"
        )
        self.assertEqual(response.status_code, 200)
        self.participant_user.refresh_from_db()
        self.assertEqual(self.participant_user.xp, 75)

        response2 = self.client.post(
            f"/api/admin/competition-participants/{self.participant.id}/mark-winner/"
        )
        self.assertEqual(response2.status_code, 200)
        self.participant_user.refresh_from_db()
        self.assertEqual(self.participant_user.xp, 75)

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, ParticipantStatus.WINNER)
