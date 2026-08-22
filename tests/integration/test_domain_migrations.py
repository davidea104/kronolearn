"""Migration and model inventory tests for the shared domain baseline."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier
from unittest import skipUnless

from django.apps import apps
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase

from gamification.models import WeeklySeason
from gamification.services.seasons import current_season


class DomainMigrationTests(TestCase):
    def test_all_shared_entities_are_installed(self):
        expected = {
            "catalog": {"ContentItem", "ContentVersion", "Choice", "LabExercise"},
            "learning": {"Enrollment", "Attempt", "Progress"},
            "gamification": {
                "ScoreEvent",
                "Streak",
                "WeeklySeason",
                "SeasonParticipation",
            },
        }
        for app_label, model_names in expected.items():
            installed = {
                model.__name__ for model in apps.get_app_config(app_label).get_models()
            }
            self.assertTrue(model_names <= installed)

    def test_shared_tables_exist_after_clean_migration(self):
        table_names = set(connection.introspection.table_names())
        expected = {
            "catalog_contentitem",
            "catalog_contentversion",
            "catalog_choice",
            "catalog_labexercise",
            "learning_enrollment",
            "learning_attempt",
            "learning_progress",
            "gamification_scoreevent",
            "gamification_streak",
            "gamification_weeklyseason",
            "gamification_seasonparticipation",
        }
        self.assertTrue(expected <= table_names)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL acceptance evidence")
class PostgreSQLSeasonIntegrityTests(TransactionTestCase):
    reset_sequences = True

    def test_weekly_seasons_cannot_overlap(self):
        WeeklySeason.objects.create(
            starts_on=date(2026, 8, 17), ends_on=date(2026, 8, 23)
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            WeeklySeason.objects.create(
                starts_on=date(2026, 8, 20), ends_on=date(2026, 8, 26)
            )

    def test_exclusion_constraint_is_installed(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT contype
                FROM pg_constraint
                WHERE conname = 'gamification_season_no_overlap'
                """
            )
            self.assertEqual(cursor.fetchone(), ("x",))

    def test_concurrent_current_season_returns_one_identity(self):
        barrier = Barrier(2)
        moment = datetime(2026, 8, 21, 12, tzinfo=UTC)

        def resolve():
            close_old_connections()
            barrier.wait()
            try:
                return current_season(moment).pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            identities = list(executor.map(lambda _: resolve(), range(2)))

        self.assertEqual(identities[0], identities[1])
        self.assertEqual(WeeklySeason.objects.count(), 1)
