"""Learner catalog HTTP visibility contracts."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from catalog.models import Module, Track


class LearnerCatalogViewTests(TestCase):
    def setUp(self):
        self.learner = Account.objects.create_user(
            email="catalog-learner@example.com",
            display_name="Catalog Learner",
            password="Strong-test-password-123",
        )
        self.active_track = Track.objects.create(
            title="Ruta visible",
            description="Descripcion visible",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        self.inactive_track = Track.objects.create(
            title="Ruta privada",
            description="Descripcion privada",
            audience="Equipo",
            position=2,
        )
        self.active_module = Module.objects.create(
            track=self.active_track,
            title="Modulo visible",
            objective="Objetivo visible",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        self.inactive_module = Module.objects.create(
            track=self.active_track,
            title="Modulo privado",
            objective="Objetivo privado",
            position=2,
        )

    def test_catalog_requires_active_session(self):
        response = self.client.get(reverse("catalog:track-list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_list_and_detail_show_only_active_hierarchy(self):
        self.client.force_login(self.learner)
        listing = self.client.get(reverse("catalog:track-list"))
        detail = self.client.get(
            reverse("catalog:track-detail", kwargs={"track_id": self.active_track.pk})
        )
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Ruta visible")
        self.assertNotContains(listing, "Ruta privada")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Modulo visible")
        self.assertNotContains(detail, "Modulo privado")
        self.assertNotContains(detail, "revision")

    def test_module_detail_validates_parent_and_active_state(self):
        self.client.force_login(self.learner)
        visible = self.client.get(
            reverse(
                "catalog:module-detail",
                kwargs={
                    "track_id": self.active_track.pk,
                    "module_id": self.active_module.pk,
                },
            )
        )
        wrong_parent = self.client.get(
            reverse(
                "catalog:module-detail",
                kwargs={
                    "track_id": self.inactive_track.pk,
                    "module_id": self.active_module.pk,
                },
            )
        )
        inactive = self.client.get(
            reverse(
                "catalog:module-detail",
                kwargs={
                    "track_id": self.active_track.pk,
                    "module_id": self.inactive_module.pk,
                },
            )
        )
        self.assertEqual(visible.status_code, 200)
        self.assertContains(visible, "Objetivo visible")
        self.assertEqual(wrong_parent.status_code, 404)
        self.assertEqual(inactive.status_code, 404)
        self.assertEqual(wrong_parent.content, inactive.content)

    def test_malformed_references_use_the_same_generic_404(self):
        self.client.force_login(self.learner)
        hidden = self.client.get(
            reverse(
                "catalog:track-detail",
                kwargs={"track_id": self.inactive_track.pk},
            )
        )
        malformed_track = self.client.get("/learn/catalog/tracks/not-a-uuid/")
        malformed_module = self.client.get(
            f"/learn/catalog/tracks/{self.active_track.pk}/modules/not-a-uuid/"
        )

        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(malformed_track.status_code, 404)
        self.assertEqual(malformed_module.status_code, 404)
        self.assertEqual(malformed_track.content, hidden.content)
        self.assertEqual(malformed_module.content, hidden.content)
        self.assertNotContains(hidden, "INACTIVE", status_code=404)
        self.assertNotContains(hidden, "revision", status_code=404)
