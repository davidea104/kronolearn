"""Learner enrollment exploration and sign-up HTTP contracts."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from catalog.models import Module, Track


class EnrollmentListAndDetailTests(TestCase):
    def setUp(self):
        self.learner = Account.objects.create_user(
            email="enrollment-learner@example.com",
            display_name="Enrollment Learner",
            password="Strong-test-password-123",
        )
        self.active_track = Track.objects.create(
            title="Track disponible",
            description="Descripcion del track disponible",
            audience="Aprendices",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        Module.objects.create(
            track=self.active_track,
            title="Modulo uno",
            objective="Objetivo uno",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        Module.objects.create(
            track=self.active_track,
            title="Modulo dos",
            objective="Objetivo dos",
            position=2,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        self.retired_track = Track.objects.create(
            title="Track retirado",
            description="Descripcion del track retirado",
            audience="Aprendices",
            position=2,
        )

    def test_list_shows_active_tracks_with_module_count(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("learning:enrollment-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Track disponible")
        self.assertContains(response, "Descripcion del track disponible")
        self.assertContains(response, "2 módulos")

    def test_list_excludes_retired_tracks(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("learning:enrollment-list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Track retirado")

    def test_detail_shows_full_track_information(self):
        self.client.force_login(self.learner)

        response = self.client.get(
            reverse(
                "learning:enrollment-detail",
                kwargs={"track_id": self.active_track.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Track disponible")
        self.assertContains(response, "Descripcion del track disponible")
        self.assertContains(response, "Modulo uno")
        self.assertContains(response, "Modulo dos")

    def test_anonymous_redirected_to_login(self):
        login_url = reverse("accounts:login")

        list_response = self.client.get(reverse("learning:enrollment-list"))
        detail_response = self.client.get(
            reverse(
                "learning:enrollment-detail",
                kwargs={"track_id": self.active_track.pk},
            )
        )

        self.assertEqual(list_response.status_code, 302)
        self.assertIn(login_url, list_response.url)
        self.assertEqual(detail_response.status_code, 302)
        self.assertIn(login_url, detail_response.url)
