"""Read-only administrative surfaces for catalog history."""

from django.contrib import admin
from django.test import RequestFactory, TestCase

from accounts.models import Account
from catalog.models import CatalogChangeLog, ModuleVersion, TrackVersion


class CatalogHistoryAdminTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.request.user = Account.objects.create_superuser(
            email="admin@example.com",
            display_name="Admin",
            password="Strong-test-password-123",
        )

    def test_history_models_are_registered_read_only(self):
        for model in (TrackVersion, ModuleVersion, CatalogChangeLog):
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_add_permission(self.request))
            self.assertFalse(model_admin.has_change_permission(self.request))
            self.assertFalse(model_admin.has_delete_permission(self.request))
            self.assertEqual(model._meta.default_permissions, ("view",))
