"""Learner-home access contract."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from catalog.models import Track
from learning.models import Enrollment
from tests.factories.catalog import module_factory


class LearnerHomeTests(TestCase):
    def home_url(self):
        try:
            return reverse("ui:learner-home")
        except NoReverseMatch:
            self.fail("ui:learner-home route must exist")

    def test_anonymous_access_redirects_to_login_without_private_content(self):
        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 302)
        expected_url = f"{reverse('accounts:login')}?next={self.home_url()}"
        self.assertEqual(response.url, expected_url)
        self.assertNotContains(response, "Learner One", status_code=302)

    def test_authenticated_account_sees_private_learner_home(self):
        account = get_user_model().objects.create_user(
            email="learner@example.com",
            display_name="Learner One",
            password="correct-horse-battery-staple",
        )
        self.client.force_login(account)

        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Learner One")

    def test_account_without_enrollments_sees_only_empty_state_catalog_action(self):
        account = get_user_model().objects.create_user(
            email="empty-learner@example.com",
            display_name="Empty Learner",
            password="correct-horse-battery-staple",
        )
        self.client.force_login(account)

        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ui/components/empty_state.html", count=1)
        self.assertContains(response, "Aún no tienes tracks inscritos")
        self.assertNotContains(response, 'class="card ')
        self.assertContains(response, f'href="{reverse("catalog:track-list")}"')

    def test_lists_only_own_tracks_with_counts_and_independent_session_actions(self):
        account = get_user_model().objects.create_user(
            email="listed-learner@example.com",
            display_name="Listed Learner",
            password="correct-horse-battery-staple",
        )
        other_account = get_user_model().objects.create_user(
            email="other-learner@example.com",
            display_name="Other Learner",
            password="correct-horse-battery-staple",
        )
        first_track = Track.objects.create(
            title="First Shared Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        second_track = Track.objects.create(
            title="Second Shared Track",
            description="Description",
            audience="Learners",
            position=2,
        )
        private_track = Track.objects.create(
            title="Other Account Private Track",
            description="Description",
            audience="Learners",
            position=3,
        )
        Track.objects.filter(pk__in=(first_track.pk, second_track.pk)).update(
            title="Shared Track"
        )
        module_factory(track=second_track, title="First Module", position=1)
        module_factory(track=second_track, title="Second Module", position=2)
        Enrollment.objects.create(account=account, track=first_track)
        Enrollment.objects.create(account=account, track=second_track)
        Enrollment.objects.create(account=other_account, track=private_track)
        self.client.force_login(account)

        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared Track", count=2)
        self.assertContains(response, "0 módulos")
        self.assertContains(response, "2 módulos")
        self.assertContains(
            response,
            reverse("learning:session-current", kwargs={"track_id": first_track.pk}),
        )
        self.assertContains(
            response,
            reverse("learning:session-current", kwargs={"track_id": second_track.pk}),
        )
        self.assertNotContains(response, private_track.title)
        self.assertTemplateUsed(response, "ui/components/card.html", count=2)
        self.assertTemplateUsed(response, "ui/components/button.html", count=2)

    def test_escapes_track_markup_and_excludes_unrequested_metrics(self):
        account = get_user_model().objects.create_user(
            email="escaped-learner@example.com",
            display_name="Escaped Learner",
            password="correct-horse-battery-staple",
        )
        track = Track.objects.create(
            title="<em>Unsafe Track</em>",
            description="Description",
            audience="Learners",
            position=1,
        )
        Enrollment.objects.create(account=account, track=track)
        self.client.force_login(account)

        response = self.client.get(self.home_url())

        self.assertContains(response, "&lt;em&gt;Unsafe Track&lt;/em&gt;")
        self.assertNotContains(response, "<em>Unsafe Track</em>")
        for excluded_label in ("Progreso", "Puntos", "Racha", "Recomendaciones"):
            with self.subTest(label=excluded_label):
                self.assertNotContains(response, excluded_label)

    def test_inactive_account_does_not_receive_private_enrollment_content(self):
        account = get_user_model().objects.create_user(
            email="inactive-learner@example.com",
            display_name="Inactive Learner",
            password="correct-horse-battery-staple",
        )
        track = Track.objects.create(
            title="Inactive Account Private Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        Enrollment.objects.create(account=account, track=track)
        self.client.force_login(account)
        get_user_model().objects.filter(pk=account.pk).update(is_active=False)

        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 302)
        self.assertNotContains(response, track.title, status_code=302)

    def test_valid_login_without_next_redirects_to_learner_home(self):
        get_user_model().objects.create_user(
            email="login-destination@example.com",
            display_name="Login Destination",
            password="correct-horse-battery-staple",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "login-destination@example.com",
                "password": "correct-horse-battery-staple",
            },
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, self.home_url())
