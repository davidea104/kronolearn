"""Own-profile isolation and editing contracts."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import NoReverseMatch, reverse

from accounts.forms import ProfileForm

VALID_PASSWORD = "correct-horse-battery-staple"


class OwnProfileTests(TestCase):
    def setUp(self):
        account_class = get_user_model()
        self.first = account_class.objects.create_user(
            email="first@example.com",
            display_name="First Learner",
            password=VALID_PASSWORD,
        )
        self.second = account_class.objects.create_user(
            email="second@example.com",
            display_name="Second Learner",
            password=VALID_PASSWORD,
        )
        self.first_client = Client()
        self.second_client = Client()
        self.first_client.force_login(self.first)
        self.second_client.force_login(self.second)

    def profile_url(self):
        try:
            return reverse("accounts:profile")
        except NoReverseMatch:
            self.fail("accounts:profile route must exist")

    def test_two_sessions_see_only_their_own_profile(self):
        url = self.profile_url()

        first_response = self.first_client.get(url, {"account_id": str(self.second.pk)})
        second_response = self.second_client.get(url, {"user_id": str(self.first.pk)})

        self.assertContains(first_response, "first@example.com")
        self.assertContains(first_response, "First Learner")
        self.assertNotContains(first_response, "second@example.com")
        self.assertContains(second_response, "second@example.com")
        self.assertContains(second_response, "Second Learner")
        self.assertNotContains(second_response, "first@example.com")

    def test_extra_identifiers_and_privileged_fields_are_ignored(self):
        response = self.first_client.post(
            self.profile_url(),
            {
                "display_name": "Updated Learner",
                "account_id": str(self.second.pk),
                "user_id": str(self.second.pk),
                "email": "stolen@example.com",
                "groups": [],
                "is_superuser": True,
                "password": "not-a-hash",
            },
        )

        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.first.display_name, "Updated Learner")
        self.assertEqual(self.first.email, "first@example.com")
        self.assertFalse(self.first.is_superuser)
        self.assertTrue(self.first.check_password(VALID_PASSWORD))
        self.assertEqual(self.second.display_name, "Second Learner")

    def test_invalid_display_names_change_nothing(self):
        for display_name in (" " * 3, "x" * 101):
            with self.subTest(display_name=display_name):
                response = self.first_client.post(
                    self.profile_url(),
                    {"display_name": display_name, "email": "changed@example.com"},
                )

                self.first.refresh_from_db()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.first.display_name, "First Learner")
                self.assertEqual(self.first.email, "first@example.com")

    def test_profile_route_contains_no_account_identifier(self):
        self.assertEqual(self.profile_url(), "/accounts/profile/")

    def test_profile_save_does_not_restore_concurrently_revoked_state(self):
        stale_account = get_user_model().objects.get(pk=self.first.pk)
        form = ProfileForm(
            {"display_name": "Concurrent Update"},
            instance=stale_account,
        )
        self.assertTrue(form.is_valid())
        get_user_model().objects.filter(pk=self.first.pk).update(
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )

        form.save()

        self.first.refresh_from_db()
        self.assertEqual(self.first.display_name, "Concurrent Update")
        self.assertFalse(self.first.is_active)
        self.assertFalse(self.first.is_staff)
        self.assertFalse(self.first.is_superuser)
