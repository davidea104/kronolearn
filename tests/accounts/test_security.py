"""Cross-cutting web security and disclosure contracts."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import RoleChangeLog
from accounts.security import LEARNER_ROLE, request_origin
from accounts.services.roles import change_content_role

VALID_PASSWORD = "correct-horse-battery-staple"


class WebSecurityTests(TestCase):
    def setUp(self):
        account_class = get_user_model()
        learner_group, _ = Group.objects.get_or_create(name=LEARNER_ROLE)
        self.admin = account_class.objects.create_superuser(
            email="admin@example.com",
            display_name="Platform Admin",
            password=VALID_PASSWORD,
        )
        self.learner = account_class.objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password=VALID_PASSWORD,
        )
        self.learner.groups.add(learner_group)

    def test_all_state_changing_routes_reject_missing_csrf(self):
        client = Client(enforce_csrf_checks=True)
        routes = [
            (
                reverse("accounts:register"),
                {
                    "email": "new@example.com",
                    "display_name": "New Learner",
                    "password1": VALID_PASSWORD,
                    "password2": VALID_PASSWORD,
                },
            ),
            (
                reverse("accounts:login"),
                {"username": self.learner.email, "password": VALID_PASSWORD},
            ),
        ]
        for url, payload in routes:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, payload).status_code, 403)

        client.force_login(self.admin)
        private_routes = (
            (reverse("accounts:profile"), {"display_name": "Changed"}),
            (reverse("accounts:logout"), {}),
            (
                reverse(
                    "accounts:assign-content-role",
                    args=(self.learner.pk,),
                ),
                {},
            ),
        )
        for url, payload in private_routes:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, payload).status_code, 403)

    def test_successful_state_changes_use_303(self):
        registration = self.client.post(
            reverse("accounts:register"),
            {
                "email": "new@example.com",
                "display_name": "New Learner",
                "password1": VALID_PASSWORD,
                "password2": VALID_PASSWORD,
            },
        )
        login = self.client.post(
            reverse("accounts:login"),
            {"username": self.learner.email, "password": VALID_PASSWORD},
        )
        profile = self.client.post(
            reverse("accounts:profile"),
            {"display_name": "Updated Learner"},
        )
        logout = self.client.post(reverse("accounts:logout"))
        self.client.force_login(self.admin)
        role_change = self.client.post(
            reverse("accounts:assign-content-role", args=(self.learner.pk,))
        )

        self.assertEqual(
            [
                registration.status_code,
                login.status_code,
                profile.status_code,
                logout.status_code,
                role_change.status_code,
            ],
            [303, 303, 303, 303, 303],
        )

    def test_forms_have_labels_csrf_and_accessible_error_summary(self):
        for route_name in ("accounts:register", "accounts:login"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertContains(response, "<label", html=False)
                self.assertContains(response, "csrfmiddlewaretoken")

        invalid = self.client.post(
            reverse("accounts:register"),
            {
                "email": "invalid",
                "display_name": "",
                "password1": "short",
                "password2": "different",
            },
        )
        self.assertContains(invalid, 'role="alert"')

        self.client.force_login(self.admin)
        role_list = self.client.get(reverse("accounts:role-management"))
        self.assertContains(role_list, "<table>")
        self.assertContains(role_list, 'scope="col"')
        self.assertContains(role_list, "csrfmiddlewaretoken")

    def test_passwords_and_session_internals_are_not_reflected(self):
        submitted_password = "never-reflect-this-password"
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.learner.email, "password": submitted_password},
        )
        body = response.content.decode()

        self.assertNotIn(submitted_password, body)
        self.assertNotIn("_auth_user_id", body)
        self.assertNotIn("sessionid", body.lower())

    def test_role_events_and_audits_never_contain_raw_target_reference(self):
        malformed = "sensitive-target-reference"

        with self.assertLogs("accounts.services.roles", level="INFO") as captured:
            change_content_role(
                self.admin,
                malformed,
                RoleChangeLog.Action.ASSIGN,
            )

        log = RoleChangeLog.objects.get()
        self.assertNotIn(malformed, str(log.__dict__))
        self.assertNotIn(malformed, " ".join(captured.output))
        self.assertNotIn(self.admin.email, " ".join(captured.output))

    def test_login_events_never_contain_raw_email_origin_or_password(self):
        origin = "203.0.113.47"
        password = "wrong-password-secret"

        with self.assertLogs("accounts", level="INFO") as captured:
            self.client.post(
                reverse("accounts:login"),
                {"username": self.learner.email, "password": password},
                REMOTE_ADDR=origin,
            )

        output = " ".join(captured.output)
        self.assertNotIn(self.learner.email, output)
        self.assertNotIn(origin, output)
        self.assertNotIn(password, output)

    def test_registration_email_enables_email_autocomplete(self):
        self.assertEqual(
            RegistrationForm().fields["email"].widget.attrs["autocomplete"],
            "email",
        )

    def test_registration_communicates_password_minimum_before_submission(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertContains(response, "Usa al menos 15 caracteres.")
        self.assertContains(response, 'id="id_password1_helptext"')
        self.assertContains(
            response,
            'aria-describedby="id_password1_helptext"',
        )

    def test_registration_uses_correct_spanish_orthography(self):
        response = self.client.get(reverse("accounts:register"))

        for text in (
            "Iniciar sesión",
            "contraseña",
            "Correo electrónico",
            "Contraseña",
            "Confirmar contraseña",
        ):
            with self.subTest(text=text):
                self.assertContains(response, text)

    @override_settings(LOGIN_TRUSTED_PROXY_COUNT=0)
    def test_untrusted_forwarded_origin_is_ignored(self):
        request = RequestFactory().post(
            "/accounts/login/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.40, 203.0.113.50",
        )

        self.assertEqual(request_origin(request), "192.0.2.10")

    @override_settings(LOGIN_TRUSTED_PROXY_COUNT=1)
    def test_trusted_proxy_uses_rightmost_forwarded_origin(self):
        request = RequestFactory().post(
            "/accounts/login/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.40, 203.0.113.50",
        )

        self.assertEqual(request_origin(request), "203.0.113.50")
