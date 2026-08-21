"""Foundational model and security contracts for accounts."""

import importlib
import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


def load_module(test_case: TestCase, module_name: str):
    """Load a wished-for module as an assertion failure when absent."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        test_case.fail(f"Foundational accounts module is missing: {exc.name}")


class AccountModelTests(TestCase):
    def test_account_uses_uuid_and_canonical_unique_email(self):
        models = load_module(self, "accounts.models")
        security = load_module(self, "accounts.security")
        account_class = getattr(models, "Account", None)
        self.assertIsNotNone(account_class, "accounts.Account must exist")

        email_field = account_class._meta.get_field("email")
        self.assertEqual(account_class._meta.pk.get_internal_type(), "UUIDField")
        self.assertTrue(email_field.unique)
        self.assertEqual(account_class.USERNAME_FIELD, "email")
        self.assertNotIn(
            "username", {field.name for field in account_class._meta.fields}
        )
        self.assertEqual(
            security.canonicalize_account_email("  Learner@Example.COM "),
            "learner@example.com",
        )

    def test_manager_canonicalizes_supported_creation_paths(self):
        models = load_module(self, "accounts.models")

        learner = models.Account.objects.create_user(
            email="  Learner@Example.COM ",
            display_name="Learner",
            password="a-valid-password-value",
        )
        admin = models.Account.objects.create_superuser(
            email="  ADMIN@Example.COM ",
            display_name="Admin",
            password="a-valid-password-value",
        )

        self.assertEqual(learner.email, "learner@example.com")
        self.assertEqual(admin.email, "admin@example.com")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_database_rejects_duplicate_canonical_email(self):
        models = load_module(self, "accounts.models")
        models.Account.objects.create_user(
            email="learner@example.com",
            display_name="One",
            password="a-valid-password-value",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            models.Account.objects.create_user(
                email=" LEARNER@EXAMPLE.COM ",
                display_name="Two",
                password="a-valid-password-value",
            )

    def test_direct_model_save_canonicalizes_email_before_unique_check(self):
        models = load_module(self, "accounts.models")
        first = models.Account(
            email=" Direct@Example.COM ",
            display_name="Direct",
        )
        first.set_password("a-valid-password-value")
        first.save()

        self.assertEqual(first.email, "direct@example.com")
        duplicate = models.Account(
            email="DIRECT@EXAMPLE.COM",
            display_name="Duplicate",
        )
        duplicate.set_password("a-valid-password-value")
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

    def test_database_rejects_case_variant_from_bulk_update(self):
        models = load_module(self, "accounts.models")
        models.Account.objects.create_user(
            email="canonical@example.com",
            display_name="Canonical",
            password="a-valid-password-value",
        )
        other = models.Account.objects.create_user(
            email="other@example.com",
            display_name="Other",
            password="a-valid-password-value",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            models.Account.objects.filter(pk=other.pk).update(
                email="CANONICAL@EXAMPLE.COM"
            )

    def test_display_name_is_required_and_bounded(self):
        models = load_module(self, "accounts.models")
        field = models.Account._meta.get_field("display_name")
        self.assertEqual(field.max_length, 100)
        self.assertFalse(field.blank)

        account = models.Account(email="learner@example.com", display_name="")
        with self.assertRaises(ValidationError):
            account.full_clean(exclude={"password"})

    def test_role_and_throttle_models_expose_required_constraints(self):
        models = load_module(self, "accounts.models")
        throttle_fields = {
            field.name for field in models.LoginThrottleBucket._meta.fields
        }
        role_log_fields = {field.name for field in models.RoleChangeLog._meta.fields}
        constraint_names = {
            constraint.name
            for model in (models.LoginThrottleBucket, models.RoleChangeLog)
            for constraint in model._meta.constraints
        }

        self.assertTrue(
            {"scope", "key_digest", "failure_count", "last_failed_at", "blocked_until"}
            <= throttle_fields
        )
        self.assertTrue(
            {
                "actor",
                "target",
                "requested_target_digest",
                "action",
                "result",
                "changed",
                "occurred_at",
            }
            <= role_log_fields
        )
        self.assertTrue(
            {
                "accounts_throttle_scope_digest_unique",
                "accounts_throttle_failure_count_positive",
                "accounts_role_target_xor_digest",
                "accounts_role_not_found_iff_target_null",
                "accounts_role_failed_never_changed",
                "accounts_role_changed_requires_success",
            }
            <= constraint_names
        )

    def test_hmac_references_are_deterministic_and_purpose_separated(self):
        security = load_module(self, "accounts.security")
        target = str(uuid.uuid4())

        first = security.security_digest(target, purpose="role-target")
        repeated = security.security_digest(target, purpose="role-target")
        throttle = security.security_digest(target, purpose="login-account")

        self.assertEqual(first, repeated)
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, target)
        self.assertNotEqual(first, throttle)
