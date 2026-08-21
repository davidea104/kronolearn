"""Django configuration and seeded-role contracts."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase


class AccountConfigurationTests(TestCase):
    def test_custom_account_model_is_configured(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.Account")

    def test_password_policy_requires_fifteen_characters(self):
        minimum_validators = [
            validator
            for validator in settings.AUTH_PASSWORD_VALIDATORS
            if validator["NAME"].endswith("MinimumLengthValidator")
        ]

        self.assertEqual(len(minimum_validators), 1)
        self.assertEqual(minimum_validators[0].get("OPTIONS", {}).get("min_length"), 15)

    def test_canonical_groups_are_seeded(self):
        self.assertTrue(Group.objects.filter(name="learner").exists())
        self.assertTrue(Group.objects.filter(name="content_admin").exists())
