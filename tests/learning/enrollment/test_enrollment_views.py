"""Learner enrollment exploration and sign-up HTTP contracts."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from catalog.models import Module, Track
from learning.models import Enrollment


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

    # --- T004 tests for enrollment POST behavior (User Story 2) ---
    def test_enroll_creates_exactly_one_enrollment(self):
        self.client.force_login(self.learner)

        enroll_url = reverse(
            "learning:enrollment-enroll",
            kwargs={"track_id": self.active_track.pk},
        )

        response = self.client.post(enroll_url)

        # Non-HTMX plain POST should redirect (see other tasks for exact behavior)
        self.assertIn(response.status_code, (302, 303))
        rows = Enrollment.objects.filter(account=self.learner, track=self.active_track)
        self.assertEqual(rows.count(), 1)

    def test_sequential_double_submit_stays_single_enrollment(self):
        self.client.force_login(self.learner)

        enroll_url = reverse(
            "learning:enrollment-enroll",
            kwargs={"track_id": self.active_track.pk},
        )

        self.client.post(enroll_url)
        self.client.post(enroll_url)
        rows = Enrollment.objects.filter(account=self.learner, track=self.active_track)
        self.assertEqual(rows.count(), 1)

    def test_two_accounts_enroll_independently(self):
        other = Account.objects.create_user(
            email="other-learner@example.com",
            display_name="Other Learner",
            password="Strong-test-password-123",
        )

        self.client.force_login(self.learner)
        enroll_url = reverse(
            "learning:enrollment-enroll", kwargs={"track_id": self.active_track.pk}
        )
        self.client.post(enroll_url)

        self.client.logout()
        self.client.force_login(other)
        self.client.post(enroll_url)
        rows_all = Enrollment.objects.filter(track=self.active_track)
        self.assertEqual(rows_all.count(), 2)

    def test_htmx_enroll_returns_track_card_partial(self):
        self.client.force_login(self.learner)
        enroll_url = reverse(
            "learning:enrollment-enroll", kwargs={"track_id": self.active_track.pk}
        )

        response = self.client.post(enroll_url, HTTP_HX_REQUEST="true")

        # HTMX requests should return a 200 with the partial HTML fragment
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"track-card-{self.active_track.pk}", response.content.decode())

    def test_anonymous_enroll_redirected_to_login(self):
        enroll_url = reverse(
            "learning:enrollment-enroll", kwargs={"track_id": self.active_track.pk}
        )

        response = self.client.post(enroll_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_account_cannot_see_another_accounts_enrollment_status(self):
        other = Account.objects.create_user(
            email="other-learner2@example.com",
            display_name="Other Learner 2",
            password="Strong-test-password-123",
        )
        # Enroll 'other' (create DB row directly for setup)
        Enrollment.objects.create(account=other, track=self.active_track)

        # Login as self.learner and request list/detail
        self.client.force_login(self.learner)

        list_resp = self.client.get(reverse("learning:enrollment-list"))
        detail_resp = self.client.get(
            reverse(
                "learning:enrollment-detail", kwargs={"track_id": self.active_track.pk}
            )
        )

        # The responses should not indicate that the logged-in account is enrolled
        self.assertNotIn("Inscrito", list_resp.content.decode())
        self.assertNotIn("Inscrito", detail_resp.content.decode())

    def test_spoofed_account_field_in_enroll_post_is_ignored(self):
        self.client.force_login(self.learner)
        enroll_url = reverse(
            "learning:enrollment-enroll", kwargs={"track_id": self.active_track.pk}
        )
        # Attempt to spoof the account by sending an account id in POST data
        self.client.post(enroll_url, data={"account": 9999})

        rows = Enrollment.objects.filter(track=self.active_track)
        # Only one enrollment should exist and it must belong to the logged-in account
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.first().account, self.learner)

    def test_retired_and_nonexistent_track_detail_return_identical_rejection(self):
        """Detail for retired track and for a nonexistent id return identical bytes."""
        self.client.force_login(self.learner)

        retired_resp = self.client.get(
            reverse(
                "learning:enrollment-detail", kwargs={"track_id": self.retired_track.pk}
            )
        )

        nonexistent_resp = self.client.get(
            reverse("learning:enrollment-detail", kwargs={"track_id": 99999})
        )

        self.assertEqual(retired_resp.status_code, nonexistent_resp.status_code)
        self.assertEqual(retired_resp.content, nonexistent_resp.content)

    def test_retired_and_nonexistent_track_enroll_return_identical_rejection_without_enrolling(
        self,
    ):
        """POST enroll to retired and to nonexistent id return identical bytes and do not create Enrollment."""
        self.client.force_login(self.learner)

        enroll_retired = self.client.post(
            reverse(
                "learning:enrollment-enroll", kwargs={"track_id": self.retired_track.pk}
            )
        )

        enroll_nonexistent = self.client.post(
            reverse("learning:enrollment-enroll", kwargs={"track_id": 99999})
        )

        self.assertEqual(enroll_retired.status_code, enroll_nonexistent.status_code)
        self.assertEqual(enroll_retired.content, enroll_nonexistent.content)

        # Assert no Enrollment was created for either attempt
        rows = Enrollment.objects.filter(track=self.retired_track)
        self.assertEqual(rows.count(), 0)
