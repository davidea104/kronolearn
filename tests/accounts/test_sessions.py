"""Authentication session and safe-return contracts."""

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.test import Client, TestCase
from django.urls import NoReverseMatch, resolve, reverse

from accounts.forms import ThrottledAuthenticationForm
from accounts.security import SAFE_RETURN_ROUTES

VALID_PASSWORD = "correct-horse-battery-staple"
GENERIC_FAILURE = "No fue posible iniciar sesión con los datos proporcionados."


def named_url(test_case, name):
    try:
        return reverse(name)
    except NoReverseMatch:
        test_case.fail(f"{name} route must exist")


class LoginViewTests(TestCase):
    def setUp(self):
        self.account = get_user_model().objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password=VALID_PASSWORD,
        )

    def test_valid_login_creates_session_and_redirects_with_303(self):
        response = self.client.post(
            named_url(self, "accounts:login"),
            {"username": " LEARNER@EXAMPLE.COM ", "password": VALID_PASSWORD},
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, named_url(self, "ui:learner-home"))
        self.assertEqual(
            str(self.client.session["_auth_user_id"]), str(self.account.pk)
        )

    def test_throttled_form_extends_django_authentication_form(self):
        self.assertTrue(issubclass(ThrottledAuthenticationForm, AuthenticationForm))

    def test_login_route_uses_django_login_view(self):
        route = resolve(named_url(self, "accounts:login"))
        view_class = getattr(route.func, "view_class", object)

        self.assertTrue(issubclass(view_class, LoginView))

    def test_invalid_and_unknown_accounts_share_generic_response(self):
        responses = []
        for index, username in enumerate(
            ("learner@example.com", "unknown@example.com"), start=10
        ):
            responses.append(
                self.client.post(
                    named_url(self, "accounts:login"),
                    {"username": username, "password": "wrong-password-value"},
                    REMOTE_ADDR=f"192.0.2.{index}",
                )
            )

        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, GENERIC_FAILURE)

    def test_active_delay_returns_429_and_retry_after(self):
        url = named_url(self, "accounts:login")
        credentials = {
            "username": "learner@example.com",
            "password": "wrong-password-value",
        }
        first = self.client.post(url, credentials, REMOTE_ADDR="192.0.2.11")
        second = self.client.post(url, credentials, REMOTE_ADDR="192.0.2.11")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertGreaterEqual(int(second["Retry-After"]), 1)
        self.assertContains(second, GENERIC_FAILURE, status_code=429)

    def test_safe_internal_next_is_used_and_external_next_falls_back(self):
        home = named_url(self, "ui:learner-home")
        login_url = named_url(self, "accounts:login")

        safe = self.client.post(
            login_url,
            {
                "username": "learner@example.com",
                "password": VALID_PASSWORD,
                "next": home,
            },
        )
        self.client.logout()
        external = self.client.post(
            login_url,
            {
                "username": "learner@example.com",
                "password": VALID_PASSWORD,
                "next": "https://example.org/steal",
            },
        )

        self.assertEqual(safe.status_code, 303)
        self.assertEqual(safe.url, home)
        self.assertEqual(external.status_code, 303)
        self.assertEqual(external.url, home)

    def test_unauthorized_internal_next_falls_back(self):
        response = self.client.post(
            named_url(self, "accounts:login"),
            {
                "username": "learner@example.com",
                "password": VALID_PASSWORD,
                "next": named_url(self, "accounts:role-management"),
            },
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, named_url(self, "ui:learner-home"))

    def test_safe_return_policy_cannot_be_modified_at_runtime(self):
        original_predicate = SAFE_RETURN_ROUTES["accounts:profile"]

        with self.assertRaises(TypeError):
            SAFE_RETURN_ROUTES["accounts:profile"] = lambda user: False

        self.assertTrue(original_predicate(self.account))


class LogoutAndPrivateSessionTests(TestCase):
    def setUp(self):
        self.account = get_user_model().objects.create_user(
            email="private@example.com",
            display_name="Private Learner",
            password=VALID_PASSWORD,
        )

    def test_private_profile_redirects_anonymous_without_content(self):
        response = self.client.get(named_url(self, "accounts:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(named_url(self, "accounts:login"), response.url)
        self.assertNotContains(response, "private@example.com", status_code=302)

    def test_logout_post_invalidates_session_and_is_idempotent(self):
        self.client.force_login(self.account)
        logout_url = named_url(self, "accounts:logout")

        first = self.client.post(logout_url)
        private_after = self.client.get(named_url(self, "accounts:profile"))
        repeated = self.client.post(logout_url)

        self.assertEqual(first.status_code, 303)
        self.assertEqual(private_after.status_code, 302)
        self.assertEqual(repeated.status_code, 303)

    def test_logout_get_is_not_allowed(self):
        self.assertEqual(
            self.client.get(named_url(self, "accounts:logout")).status_code,
            405,
        )

    def test_logout_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.account)

        response = csrf_client.post(named_url(self, "accounts:logout"))

        self.assertEqual(response.status_code, 403)

    def test_expired_session_loses_private_access(self):
        self.client.force_login(self.account)
        session = self.client.session
        session.set_expiry(-1)
        session.save()

        response = self.client.get(named_url(self, "accounts:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(named_url(self, "accounts:login"), response.url)

    def test_deactivated_account_loses_private_access(self):
        self.client.force_login(self.account)
        get_user_model().objects.filter(pk=self.account.pk).update(is_active=False)

        response = self.client.get(named_url(self, "ui:learner-home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(named_url(self, "accounts:login"), response.url)
