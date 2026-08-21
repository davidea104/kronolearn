"""Learner-home access contract."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class LearnerHomeTests(TestCase):
    def home_url(self):
        try:
            return reverse("ui:learner-home")
        except NoReverseMatch:
            self.fail("ui:learner-home route must exist")

    def test_anonymous_access_redirects_to_login_without_private_content(self):
        response = self.client.get(self.home_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
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
