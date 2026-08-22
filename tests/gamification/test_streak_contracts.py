"""Contract tests for streak services."""

import inspect
from datetime import date

from django.test import SimpleTestCase

from gamification.services.streaks import (
    STREAK_BONUS_CAP,
    STREAK_BONUS_STEP,
    register_activity,
    streak_bonus,
)


class StreakContractTests(SimpleTestCase):
    def test_constants_and_public_signatures_are_stable(self):
        self.assertEqual(STREAK_BONUS_STEP, 10)
        self.assertEqual(STREAK_BONUS_CAP, 50)
        self.assertEqual(
            tuple(inspect.signature(register_activity).parameters),
            ("account", "activity_date"),
        )
        self.assertEqual(tuple(inspect.signature(streak_bonus).parameters), ("streak",))

    def test_operations_are_side_effect_free_stubs(self):
        with self.assertRaises(NotImplementedError):
            register_activity(object(), date(2026, 8, 21))
        with self.assertRaises(NotImplementedError):
            streak_bonus(object())
