"""Cross-page consistency contract for the light/dark theme toggle."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ThemeToggleConsistencyTests(TestCase):
    def test_toggle_present_on_login(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, "data-theme-toggle")

    def test_toggle_present_on_register(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertContains(response, "data-theme-toggle")

    def test_toggle_present_on_learner_home(self):
        account = get_user_model().objects.create_user(
            email="theme-learner@example.com",
            display_name="Theme Learner",
            password="correct-horse-battery-staple",
        )
        self.client.force_login(account)

        response = self.client.get(reverse("ui:learner-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-theme-toggle")

    def test_toggle_absent_from_django_admin_login(self):
        response = self.client.get(reverse("admin:login"))

        self.assertNotContains(response, "data-theme-toggle")
        self.assertNotContains(response, "kronolearn:theme")
