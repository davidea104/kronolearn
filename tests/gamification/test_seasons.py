"""Contract tests for canonical weekly seasons and leaderboard projections."""

import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

from django.test import TestCase

from gamification.services.seasons import LeaderboardEntry, current_season, leaderboard


class SeasonContractTests(TestCase):
    def test_current_season_uses_project_week_and_rejects_naive_datetimes(self):
        season = current_season(datetime(2026, 8, 23, 3, 30, tzinfo=UTC))
        self.assertEqual(season.starts_on.isoformat(), "2026-08-17")
        self.assertEqual(season.ends_on.isoformat(), "2026-08-23")
        self.assertEqual(
            current_season(datetime(2026, 8, 17, 12, tzinfo=UTC)).pk, season.pk
        )
        with self.assertRaises(ValueError):
            current_season(datetime(2026, 8, 21, 12))  # noqa: DTZ001

    def test_leaderboard_projection_is_frozen_and_privacy_preserving(self):
        entry = LeaderboardEntry(
            display_name="Public Name",
            position=1,
            weekly_points=100,
            correct_scoreable_attempts=1,
            total_scoreable_attempts=2,
            completed_sessions=3,
        )
        self.assertNotIn("email", entry.__dataclass_fields__)
        self.assertNotIn("account_id", entry.__dataclass_fields__)
        with self.assertRaises(FrozenInstanceError):
            entry.position = 2

    def test_leaderboard_signature_and_stub(self):
        self.assertEqual(tuple(inspect.signature(leaderboard).parameters), ("season",))
        with self.assertRaises(NotImplementedError):
            leaderboard(object())
