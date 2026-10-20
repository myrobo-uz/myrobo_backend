from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Tag
from apps.users.models import User

from .models import Project, ProjectStatus


def _make_user(telegram_id=1, phone="+998900000001", full_name="Test User"):
    return User.objects.create(telegram_id=telegram_id, phone_number=phone, full_name=full_name)


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = _make_user()
        self.other_user = _make_user(telegram_id=2, phone="+998900000002", full_name="Boshqa User")
        self.owner_token = RefreshToken.for_user(self.owner).access_token
        self.other_token = RefreshToken.for_user(self.other_user).access_token

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_project_requires_authentication(self):
        client = APIClient()
        response = client.post("/projects/create/", {"title": "Robot qo'li"})
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_create_project(self):
        self._auth(self.owner_token)
        response = self.client.post("/projects/create/", {"title": "Robot qo'li", "description": "Qo'l prototipi"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get("slug"), "create response must return slug for client navigation")
        project = Project.objects.get(id=response.data["id"])
        self.assertEqual(project.user, self.owner)
        self.assertEqual(project.status, ProjectStatus.ACTIVE)
        self.assertEqual(project.slug, response.data["slug"])

    def test_public_list_excludes_archived_projects(self):
        Project.objects.create(user=self.owner, title="Faol loyiha", status=ProjectStatus.ACTIVE)
        Project.objects.create(user=self.owner, title="Arxiv loyiha", status=ProjectStatus.ARCHIVED)

        client = APIClient()
        response = client.get("/projects/")
        titles = [p["title"] for p in response.data["results"]]
        self.assertIn("Faol loyiha", titles)
        self.assertNotIn("Arxiv loyiha", titles)

    def test_search_filters_by_title(self):
        Project.objects.create(user=self.owner, title="Arduino robot", status=ProjectStatus.ACTIVE)
        Project.objects.create(user=self.owner, title="Veb sayt", status=ProjectStatus.ACTIVE)

        client = APIClient()
        response = client.get("/projects/", {"search": "arduino"})
        titles = [p["title"] for p in response.data["results"]]
        self.assertEqual(titles, ["Arduino robot"])

    def test_tag_filter(self):
        tag = Tag.objects.create(name="IoT")
        p1 = Project.objects.create(user=self.owner, title="IoT loyiha", status=ProjectStatus.ACTIVE)
        p1.tags.add(tag)
        Project.objects.create(user=self.owner, title="Boshqa loyiha", status=ProjectStatus.ACTIVE)

        client = APIClient()
        response = client.get("/projects/", {"tag": tag.slug})
        titles = [p["title"] for p in response.data["results"]]
        self.assertEqual(titles, ["IoT loyiha"])

    def test_only_owner_can_update_project(self):
        project = Project.objects.create(user=self.owner, title="Mening loyiham", status=ProjectStatus.ACTIVE)

        self._auth(self.other_token)
        response = self.client.patch(f"/projects/{project.slug}/", {"title": "Hack"}, format="json")
        self.assertEqual(response.status_code, 403)

        self._auth(self.owner_token)
        response = self.client.patch(f"/projects/{project.slug}/", {"title": "Yangilangan"}, format="json")
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.title, "Yangilangan")

    def test_marking_project_completed_awards_xp_once(self):
        project = Project.objects.create(user=self.owner, title="Loyiha", status=ProjectStatus.ACTIVE)
        self._auth(self.owner_token)

        response = self.client.patch(f"/projects/{project.slug}/", {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.xp, 50)

        # Marking completed again (no-op status change) must not double-award.
        response = self.client.patch(f"/projects/{project.slug}/", {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.xp, 50)

    def test_owner_can_delete_project(self):
        project = Project.objects.create(user=self.owner, title="O'chiriladigan", status=ProjectStatus.ACTIVE)
        self._auth(self.owner_token)
        response = self.client.delete(f"/projects/{project.slug}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_my_projects_lists_only_own_projects(self):
        Project.objects.create(user=self.owner, title="Meniki", status=ProjectStatus.ACTIVE)
        Project.objects.create(user=self.other_user, title="Boshqaniki", status=ProjectStatus.ACTIVE)

        self._auth(self.owner_token)
        response = self.client.get("/projects/my/")
        titles = [p["title"] for p in response.data["results"]]
        self.assertEqual(titles, ["Meniki"])
