"""Temporary daily-session route contract."""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class CurrentSessionPlaceholderTests(TestCase):
    def session_url(self, track_id=None):
        try:
            return reverse(
                "learning:session-current",
                kwargs={"track_id": track_id or uuid.uuid4()},
            )
        except NoReverseMatch:
            self.fail("learning:session-current must reverse with track_id")

    def test_anonymous_request_redirects_to_login_with_requested_destination(self):
        session_url = self.session_url()

        response = self.client.get(session_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertIn(f"next={session_url}", response.url)

    def test_active_account_receives_accessible_generic_placeholder(self):
        account = get_user_model().objects.create_user(
            email="session-placeholder@example.com",
            display_name="Session Learner",
            password="correct-horse-battery-staple",
        )
        track_id = uuid.uuid4()
        self.client.force_login(account)

        response = self.client.get(self.session_url(track_id))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning/session/current.html")
        self.assertContains(response, "Tu sesión estará disponible pronto")
        self.assertContains(response, reverse("ui:learner-home"))
        self.assertNotContains(response, str(track_id))
