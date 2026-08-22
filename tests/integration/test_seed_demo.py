"""End-to-end contract tests for the deterministic demo seed."""

from io import StringIO
from time import monotonic

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE, LEARNER_ROLE
from catalog.models import (
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    Track,
)
from gamification.models import WeeklySeason

DEMO_TRACK_TITLES = (
    "Crea tu registro de gastos con agentes y SDD",
    "Fundamentos de negocio para equipos técnicos",
)


@override_settings(DEBUG=True)
class SeedDemoTests(TestCase):
    def run_seed(self, **options):
        output = StringIO()
        call_command("seed_demo", stdout=output, **options)
        return output.getvalue()

    def demo_identities(self):
        return {
            "accounts": tuple(
                Account.objects.filter(email__endswith=".invalid")
                .order_by("email")
                .values_list("id", flat=True)
            ),
            "tracks": tuple(
                Track.objects.filter(title__in=DEMO_TRACK_TITLES)
                .order_by("title")
                .values_list("id", flat=True)
            ),
            "modules": tuple(
                Module.objects.filter(track__title__in=DEMO_TRACK_TITLES)
                .order_by("track__title")
                .values_list("id", flat=True)
            ),
            "contents": tuple(
                ContentItem.objects.filter(module__track__title__in=DEMO_TRACK_TITLES)
                .order_by("module__track__title")
                .values_list("id", flat=True)
            ),
            "seasons": tuple(WeeklySeason.objects.values_list("id", flat=True)),
        }

    def test_clean_seed_creates_exact_minimal_graph_under_budget(self):
        started = monotonic()
        output = self.run_seed()
        self.assertLess(monotonic() - started, 120)

        self.assertEqual(Track.objects.filter(title__in=DEMO_TRACK_TITLES).count(), 2)
        self.assertEqual(
            Module.objects.filter(track__title__in=DEMO_TRACK_TITLES).count(), 2
        )
        self.assertEqual(
            ContentItem.objects.filter(
                module__track__title__in=DEMO_TRACK_TITLES
            ).count(),
            2,
        )
        self.assertEqual(ContentVersion.objects.count(), 2)
        self.assertEqual(Choice.objects.count(), 6)
        self.assertEqual(LabExercise.objects.count(), 2)
        self.assertEqual(Account.objects.filter(email__endswith=".invalid").count(), 2)
        self.assertEqual(WeeklySeason.objects.count(), 1)
        for role in (LEARNER_ROLE, CONTENT_ADMIN_ROLE):
            self.assertEqual(
                Account.objects.filter(
                    groups__name=role, email__endswith=".invalid"
                ).count(),
                1,
            )
        self.assertIn(DEMO_TRACK_TITLES[0], output)

    def test_repeat_seed_preserves_identities_and_counts(self):
        self.run_seed()
        before = self.demo_identities()
        counts = {
            model: model.objects.count()
            for model in (
                Account,
                Track,
                Module,
                ContentItem,
                ContentVersion,
                Choice,
                LabExercise,
                WeeklySeason,
            )
        }
        self.run_seed()
        self.assertEqual(self.demo_identities(), before)
        self.assertEqual(
            {model: model.objects.count() for model in counts},
            counts,
        )

    def test_incomplete_demo_is_repaired_without_overwriting_unrelated_data(self):
        unrelated = Track.objects.create(
            title="Unrelated Track",
            description="Keep this",
            audience="Other",
            position=1,
        )
        partial = Track.objects.create(
            title=DEMO_TRACK_TITLES[0],
            description="Incomplete",
            audience="Demo",
            position=2,
        )
        self.run_seed()

        unrelated.refresh_from_db()
        partial.refresh_from_db()
        self.assertEqual(unrelated.description, "Keep this")
        self.assertEqual(partial.description, "Incomplete")
        self.assertEqual(partial.modules.count(), 1)
        self.assertEqual(partial.modules.get().content_items.count(), 1)

    @override_settings(DEBUG=False)
    def test_production_requires_confirmation_before_writes(self):
        with self.assertRaises(CommandError):
            self.run_seed()
        self.assertFalse(Account.objects.filter(email__endswith=".invalid").exists())
        self.assertFalse(Track.objects.filter(title__in=DEMO_TRACK_TITLES).exists())

    @override_settings(DEBUG=False)
    def test_confirmed_production_accounts_have_unusable_passwords(self):
        self.run_seed(confirm_production=True)
        accounts = Account.objects.filter(email__endswith=".invalid")
        self.assertEqual(accounts.count(), 2)
        self.assertTrue(all(not account.has_usable_password() for account in accounts))

    def test_output_never_exposes_private_values(self):
        output = self.run_seed()
        lowered = output.casefold()
        self.assertNotIn(".invalid", lowered)
        self.assertNotIn("password", lowered)
        self.assertNotIn("token", lowered)
        for account in Account.objects.filter(email__endswith=".invalid"):
            self.assertNotIn(account.email.casefold(), lowered)
            self.assertNotIn(str(account.pk).casefold(), lowered)
