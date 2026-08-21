"""HTTP contracts for platform content-role management."""

import uuid
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import RoleChangeLog
from accounts.security import CONTENT_ADMIN_ROLE, LEARNER_ROLE

VALID_PASSWORD = "correct-horse-battery-staple"
GENERIC_DENIAL = "No tienes permiso para realizar esta acción."


def named_url(test_case, name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs or None)
    except NoReverseMatch:
        test_case.fail(f"{name} route must exist")


class RoleManagementViewTests(TestCase):
    def setUp(self):
        account_class = get_user_model()
        learner_group, _ = Group.objects.get_or_create(name=LEARNER_ROLE)
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.admin = account_class.objects.create_superuser(
            email="admin@example.com",
            display_name="Platform Admin",
            password=VALID_PASSWORD,
        )
        self.learner = account_class.objects.create_user(
            email="learner@example.com",
            display_name="Search Needle",
            password=VALID_PASSWORD,
        )
        self.other = account_class.objects.create_user(
            email="other@example.com",
            display_name="Other Learner",
            password=VALID_PASSWORD,
        )
        self.content_admin = account_class.objects.create_user(
            email="editor@example.com",
            display_name="Content Admin",
            password=VALID_PASSWORD,
        )
        self.learner.groups.add(learner_group)
        self.other.groups.add(learner_group)
        self.content_admin.groups.add(learner_group, content_group)

    def action_url(self, name, target_ref):
        return named_url(self, name, target_ref=target_ref)

    def test_list_is_platform_admin_only_and_discloses_nothing_on_denial(self):
        url = named_url(self, "accounts:role-management")

        anonymous = self.client.get(url)
        self.client.force_login(self.learner)
        learner = self.client.get(url)
        self.client.force_login(self.content_admin)
        content_admin = self.client.get(url)
        self.client.force_login(self.admin)
        platform_admin = self.client.get(url)

        self.assertEqual(anonymous.status_code, 302)
        for response in (learner, content_admin):
            self.assertContains(response, GENERIC_DENIAL, status_code=403)
            self.assertNotContains(
                response,
                self.other.email,
                status_code=403,
            )
            self.assertNotContains(
                response,
                str(self.other.pk),
                status_code=403,
            )
        self.assertContains(platform_admin, self.learner.email)
        self.assertContains(platform_admin, str(self.learner.pk))
        self.assertContains(platform_admin, "Aprendiz")

    def test_search_uses_bounded_query_and_paginates_accounts(self):
        account_class = get_user_model()
        for index in range(30):
            account_class.objects.create_user(
                email=f"page-{index:02d}@example.com",
                display_name=f"Page Account {index:02d}",
                password=VALID_PASSWORD,
            )
        self.client.force_login(self.admin)
        url = named_url(self, "accounts:role-management")

        filtered = self.client.get(url, {"q": "needle"})
        injection_like = self.client.get(url, {"q": "' OR 1=1 --"})
        paginated = self.client.get(url)

        self.assertContains(filtered, self.learner.email)
        self.assertNotContains(filtered, self.other.email)
        self.assertNotContains(injection_like, self.learner.email)
        self.assertGreaterEqual(
            paginated.context["page_obj"].paginator.num_pages,
            2,
        )

    def test_assign_and_revoke_are_post_csrf_only_and_redirect_with_303(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        list_url = named_url(self, "accounts:role-management")
        assign_url = self.action_url(
            "accounts:assign-content-role", str(self.learner.pk)
        )
        revoke_url = self.action_url(
            "accounts:revoke-content-role", str(self.learner.pk)
        )

        missing_csrf = csrf_client.post(assign_url)
        get_attempt = csrf_client.get(assign_url)
        csrf_client.get(list_url)
        token = csrf_client.cookies["csrftoken"].value
        assigned = csrf_client.post(assign_url, HTTP_X_CSRFTOKEN=token)
        revoked = csrf_client.post(revoke_url, HTTP_X_CSRFTOKEN=token)

        self.assertEqual(missing_csrf.status_code, 403)
        self.assertEqual(get_attempt.status_code, 405)
        self.assertEqual(assigned.status_code, 303)
        self.assertEqual(assigned.url, list_url)
        self.assertEqual(revoked.status_code, 303)
        self.assertEqual(RoleChangeLog.objects.count(), 2)
        self.assertFalse(self.learner.groups.filter(name=CONTENT_ADMIN_ROLE).exists())

    def test_anonymous_action_redirects_without_audit(self):
        response = self.client.post(
            self.action_url(
                "accounts:assign-content-role",
                str(self.learner.pk),
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleChangeLog.objects.count(), 0)

    def test_self_target_and_unauthorized_existing_target_are_denied_and_audited(self):
        self.client.force_login(self.admin)
        self_target = self.client.post(
            self.action_url(
                "accounts:assign-content-role",
                str(self.admin.pk),
            )
        )
        self.client.force_login(self.learner)
        unauthorized = self.client.post(
            self.action_url(
                "accounts:assign-content-role",
                str(self.other.pk),
            )
        )

        self.assertContains(self_target, GENERIC_DENIAL, status_code=403)
        self.assertContains(unauthorized, GENERIC_DENIAL, status_code=403)
        self.assertFalse(self.other.groups.filter(name=CONTENT_ADMIN_ROLE).exists())
        self.assertEqual(RoleChangeLog.objects.count(), 2)
        self.assertEqual(
            set(RoleChangeLog.objects.values_list("result", flat=True)),
            {RoleChangeLog.Result.DENIED},
        )

    def test_missing_and_malformed_targets_hide_existence_and_audit_once(self):
        references = (str(uuid.uuid4()), "not-a-uuid")
        statuses = []

        for actor, expected_status in ((self.admin, 404), (self.learner, 403)):
            self.client.force_login(actor)
            for target_ref in references:
                response = self.client.post(
                    self.action_url(
                        "accounts:revoke-content-role",
                        target_ref,
                    )
                )
                statuses.append(response.status_code)
                self.assertNotContains(
                    response,
                    target_ref,
                    status_code=expected_status,
                )

        self.assertEqual(statuses, [404, 404, 403, 403])
        logs = list(RoleChangeLog.objects.all())
        self.assertEqual(len(logs), 4)
        self.assertTrue(
            all(log.result == RoleChangeLog.Result.TARGET_NOT_FOUND for log in logs)
        )
        self.assertTrue(all(log.target is None for log in logs))
        self.assertTrue(all(len(log.requested_target_digest) == 64 for log in logs))

    def test_not_found_response_uses_service_authority_snapshot(self):
        target_ref = str(uuid.uuid4())
        cases = (
            (self.admin, False, 403),
            (self.learner, True, 404),
        )

        for actor, actor_is_platform_admin, expected_status in cases:
            with self.subTest(
                actor=actor.email,
                actor_is_platform_admin=actor_is_platform_admin,
            ):
                self.client.force_login(actor)
                outcome = SimpleNamespace(
                    result=RoleChangeLog.Result.TARGET_NOT_FOUND,
                    actor_is_platform_admin=actor_is_platform_admin,
                )
                with patch("accounts.views.change_content_role", return_value=outcome):
                    response = self.client.post(
                        self.action_url(
                            "accounts:assign-content-role",
                            target_ref,
                        )
                    )

                self.assertEqual(response.status_code, expected_status)
