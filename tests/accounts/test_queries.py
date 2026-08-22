"""Authorized account query service contracts."""

import importlib
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.transaction import TransactionManagementError
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.test.utils import CaptureQueriesContext

from accounts.security import CONTENT_ADMIN_ROLE


class ContentAdminQueryTests(TransactionTestCase):
    def setUp(self):
        account_class = get_user_model()
        content_admin_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.content_admin = account_class.objects.create_user(
            email="content-admin@example.com",
            display_name="Content Admin",
            password="test-password",
        )
        self.content_admin.groups.add(content_admin_group)
        self.inactive_admin = account_class.objects.create_user(
            email="inactive-admin@example.com",
            display_name="Inactive Admin",
            password="test-password",
            is_active=False,
        )
        self.inactive_admin.groups.add(content_admin_group)
        self.learner = account_class.objects.create_user(
            email="learner-query@example.com",
            display_name="Learner",
            password="test-password",
        )

    def service(self):
        try:
            return importlib.import_module("accounts.services.queries")
        except ModuleNotFoundError as exc:
            self.fail(f"Account query service is missing: {exc.name}")

    def test_active_content_admin_is_resolved(self):
        resolved = self.service().resolve_content_admin(str(self.content_admin.pk))

        self.assertEqual(resolved.pk, self.content_admin.pk)

    def test_rejected_references_are_observationally_equivalent(self):
        service = self.service()
        rejected_references = (
            "",
            "not-a-uuid",
            str(uuid.uuid4()),
            str(self.inactive_admin.pk),
            str(self.learner.pk),
        )
        messages = []

        for actor_ref in rejected_references:
            with self.subTest(actor_ref=actor_ref):
                with self.assertRaises(PermissionDenied) as raised:
                    service.resolve_content_admin(actor_ref)
                messages.append(str(raised.exception))
                if actor_ref:
                    self.assertNotIn(actor_ref, str(raised.exception))

        self.assertEqual(len(set(messages)), 1)

    def test_for_update_requires_an_atomic_transaction(self):
        service = self.service()

        with self.assertRaises(TransactionManagementError):
            service.resolve_content_admin(
                str(self.content_admin.pk),
                for_update=True,
            )

    @skipUnlessDBFeature("has_select_for_update")
    def test_for_update_emits_a_row_lock(self):
        service = self.service()

        with transaction.atomic(), CaptureQueriesContext(connection) as captured:
            resolved = service.resolve_content_admin(
                str(self.content_admin.pk),
                for_update=True,
            )

        self.assertEqual(resolved.pk, self.content_admin.pk)
        self.assertTrue(
            any("FOR UPDATE" in query["sql"].upper() for query in captured),
            captured.captured_queries,
        )
