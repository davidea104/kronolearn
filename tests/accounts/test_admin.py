"""Read-only administrative role-audit contracts."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import RoleChangeLog
from accounts.security import security_digest

VALID_PASSWORD = "correct-horse-battery-staple"


class RoleChangeLogAdminTests(TestCase):
    def setUp(self):
        account_class = get_user_model()
        self.admin_account = account_class.objects.create_superuser(
            email="admin@example.com",
            display_name="Platform Admin",
            password=VALID_PASSWORD,
        )
        self.target = account_class.objects.create_user(
            email="target@example.com",
            display_name="Target",
            password=VALID_PASSWORD,
        )
        self.existing_log = RoleChangeLog.objects.create(
            actor=self.admin_account,
            target=self.target,
            action=RoleChangeLog.Action.ASSIGN,
            result=RoleChangeLog.Result.SUCCESS,
            changed=False,
        )
        self.malformed = "not-a-uuid"
        self.target_digest = security_digest(
            self.malformed,
            purpose="role-target",
        )
        self.unresolved_log = RoleChangeLog.objects.create(
            actor=self.admin_account,
            target=None,
            requested_target_digest=self.target_digest,
            action=RoleChangeLog.Action.REVOKE,
            result=RoleChangeLog.Result.TARGET_NOT_FOUND,
            changed=False,
        )

    def test_account_and_role_change_log_are_registered(self):
        self.assertIn(get_user_model(), admin.site._registry)
        self.assertIn(RoleChangeLog, admin.site._registry)

    def test_account_admin_does_not_expose_role_membership_fields(self):
        model_admin = admin.site._registry[get_user_model()]
        request = RequestFactory().get("/admin/accounts/account/")
        request.user = self.admin_account

        editable_fields = set(model_admin.get_form(request, self.target).base_fields)

        self.assertNotIn("groups", editable_fields)
        self.assertNotIn("user_permissions", editable_fields)

    def test_role_audit_admin_is_read_only(self):
        model_admin = admin.site._registry.get(RoleChangeLog)
        self.assertIsNotNone(model_admin, "RoleChangeLog admin must be registered")
        request = RequestFactory().get("/admin/accounts/rolechangelog/")
        request.user = self.admin_account

        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, self.existing_log))
        self.assertFalse(model_admin.has_delete_permission(request, self.existing_log))
        self.assertEqual(
            set(model_admin.get_readonly_fields(request, self.existing_log)),
            {
                "id",
                "actor",
                "target",
                "requested_target_digest",
                "action",
                "result",
                "changed",
                "occurred_at",
            },
        )

    def test_changelist_represents_existing_and_unresolved_targets_safely(self):
        self.client.force_login(self.admin_account)

        response = self.client.get(reverse("admin:accounts_rolechangelog_changelist"))

        self.assertContains(response, str(self.target.pk))
        self.assertContains(response, self.target_digest[:12])
        self.assertNotContains(response, self.malformed)

    def test_admin_cannot_add_update_or_delete_audit_rows(self):
        self.client.force_login(self.admin_account)
        change_url = reverse(
            "admin:accounts_rolechangelog_change",
            args=(self.existing_log.pk,),
        )
        delete_url = reverse(
            "admin:accounts_rolechangelog_delete",
            args=(self.existing_log.pk,),
        )

        add_response = self.client.get(reverse("admin:accounts_rolechangelog_add"))
        change_response = self.client.post(
            change_url,
            {"result": RoleChangeLog.Result.DENIED},
        )
        delete_response = self.client.post(delete_url, {"post": "yes"})

        self.existing_log.refresh_from_db()
        self.assertEqual(add_response.status_code, 403)
        self.assertEqual(change_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.assertEqual(self.existing_log.result, RoleChangeLog.Result.SUCCESS)
