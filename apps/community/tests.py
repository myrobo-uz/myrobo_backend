from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

from .models import CommentLike, Topic, TopicComment, TopicLike


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


class CommunityAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _make_user()
        self.other_user = _make_user(telegram_id=2, phone="+998900000002", full_name="Boshqa User")
        self.owner_token = RefreshToken.for_user(self.owner).access_token
        self.other_token = RefreshToken.for_user(self.other_user).access_token

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_topic_requires_authentication(self):
        client = APIClient()
        response = client.post("/community/topics/create/", {"title": "Savol", "description": "Matn"})
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_topic(self):
        self._auth(self.owner_token)
        response = self.client.post(
            "/community/topics/create/", {"title": "Arduino bilan muammo", "description": "Yordam kerak"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get("slug"), "create response must return slug for client navigation")
        topic = Topic.objects.get(id=response.data["id"])
        self.assertEqual(topic.user, self.owner)
        self.assertFalse(topic.is_solved)
        self.assertEqual(topic.slug, response.data["slug"])

    def test_public_list_excludes_inactive_topics(self):
        Topic.objects.create(user=self.owner, title="Faol mavzu", description="...")
        Topic.objects.create(user=self.owner, title="Yashirin mavzu", description="...", is_active=False)

        client = APIClient()
        response = client.get("/community/topics/")
        titles = [t["title"] for t in response.data["results"]]
        self.assertIn("Faol mavzu", titles)
        self.assertNotIn("Yashirin mavzu", titles)

    def test_is_solved_filter(self):
        Topic.objects.create(user=self.owner, title="Yechilgan", description="...", is_solved=True)
        Topic.objects.create(user=self.owner, title="Yechilmagan", description="...", is_solved=False)

        client = APIClient()
        response = client.get("/community/topics/", {"is_solved": "true"})
        titles = [t["title"] for t in response.data["results"]]
        self.assertEqual(titles, ["Yechilgan"])

    def test_comment_create_and_list_in_detail(self):
        topic = Topic.objects.create(user=self.owner, title="Savol", description="...")
        self._auth(self.other_token)
        response = self.client.post(f"/community/topics/{topic.slug}/comments/", {"text": "Javob matni"})
        self.assertEqual(response.status_code, 201)

        detail = self.client.get(f"/community/topics/{topic.slug}/")
        self.assertEqual(detail.data["comments"]["count"], 1)

    def test_only_topic_owner_can_accept_comment(self):
        topic = Topic.objects.create(user=self.owner, title="Savol", description="...")
        comment = TopicComment.objects.create(topic=topic, user=self.other_user, text="Yechim")

        self._auth(self.other_token)
        response = self.client.post(f"/community/comments/{comment.id}/accept/")
        self.assertEqual(response.status_code, 403)

        self._auth(self.owner_token)
        response = self.client.post(f"/community/comments/{comment.id}/accept/")
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        topic.refresh_from_db()
        self.assertTrue(comment.is_accepted)
        self.assertTrue(topic.is_solved)

    def test_topic_like_toggle(self):
        topic = Topic.objects.create(user=self.owner, title="Savol", description="...")
        self._auth(self.other_token)

        response = self.client.post(f"/community/topics/{topic.slug}/like/")
        self.assertEqual(response.data["liked"], True)
        self.assertEqual(TopicLike.objects.filter(topic=topic, user=self.other_user).count(), 1)

        response = self.client.post(f"/community/topics/{topic.slug}/like/")
        self.assertEqual(response.data["liked"], False)
        self.assertEqual(TopicLike.objects.filter(topic=topic, user=self.other_user).count(), 0)

    def test_comment_like_toggle(self):
        topic = Topic.objects.create(user=self.owner, title="Savol", description="...")
        comment = TopicComment.objects.create(topic=topic, user=self.owner, text="Birinchi izoh")
        self._auth(self.other_token)

        response = self.client.post(f"/community/comments/{comment.id}/like/")
        self.assertEqual(response.data["liked"], True)
        self.assertEqual(CommentLike.objects.filter(comment=comment, user=self.other_user).count(), 1)

    def test_popular_ordering_by_likes(self):
        popular = Topic.objects.create(user=self.owner, title="Mashhur", description="...")
        Topic.objects.create(user=self.owner, title="Kam mashhur", description="...")
        TopicLike.objects.create(topic=popular, user=self.other_user)

        client = APIClient()
        response = client.get("/community/topics/", {"ordering": "popular"})
        self.assertEqual(response.data["results"][0]["title"], "Mashhur")

    def test_only_owner_can_edit_or_delete_topic(self):
        topic = Topic.objects.create(user=self.owner, title="Savol", description="...")

        self._auth(self.other_token)
        response = self.client.patch(f"/community/topics/{topic.slug}/", {"title": "Hack"}, format="json")
        self.assertEqual(response.status_code, 403)

        self._auth(self.owner_token)
        response = self.client.delete(f"/community/topics/{topic.slug}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Topic.objects.filter(id=topic.id).exists())
