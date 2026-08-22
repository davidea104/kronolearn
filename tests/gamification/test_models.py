"""Persistence tests for gamification domain contracts."""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from gamification.models import ScoreEvent, SeasonParticipation, Streak, WeeklySeason
from tests.factories.gamification import (
    score_event_factory,
    season_participation_factory,
    streak_factory,
    weekly_season_factory,
)


class GamificationModelTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="player@example.com",
            display_name="Player",
            password="Strong-test-password-123",
        )

    def test_session_completed_receipt_uses_only_generic_constraints(self):
        receipt = ScoreEvent.objects.create(
            cause=ScoreEvent.Cause.SESSION_COMPLETED,
            amount=0,
            attempt=None,
            idempotency_digest="c" * 64,
        )
        self.assertIsNone(receipt.attempt)
        ScoreEvent.objects.create(
            cause=ScoreEvent.Cause.SESSION_COMPLETED,
            amount=1,
            attempt=None,
            idempotency_digest="d" * 64,
        )

    def test_attempt_cause_requires_attempt(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ScoreEvent.objects.create(
                cause=ScoreEvent.Cause.ATTEMPT,
                amount=100,
                attempt=None,
                idempotency_digest="e" * 64,
            )

    def test_streak_and_participation_counters_are_bounded(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Streak.objects.create(
                account=self.account,
                current_length=2,
                longest_length=1,
            )
        today = timezone.localdate()
        season = WeeklySeason.objects.create(
            starts_on=today,
            ends_on=today + timedelta(days=6),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            SeasonParticipation.objects.create(
                season=season,
                account=self.account,
                correct_scoreable_attempts=2,
                total_scoreable_attempts=1,
            )

    def test_weekly_season_requires_ordered_dates(self):
        today = timezone.localdate()
        with self.assertRaises(IntegrityError), transaction.atomic():
            WeeklySeason.objects.create(
                starts_on=today,
                ends_on=today - timedelta(days=1),
            )

    def test_gamification_factories_create_valid_defaults_and_accept_overrides(self):
        event = score_event_factory(amount=50)
        streak = streak_factory(current_length=2, longest_length=3)
        season = weekly_season_factory()
        participation = season_participation_factory(
            season=season,
            correct_scoreable_attempts=1,
            total_scoreable_attempts=2,
        )

        self.assertEqual(event.amount, 50)
        self.assertEqual(event.attempt.score_event, event)
        self.assertEqual(streak.current_length, 2)
        self.assertEqual(participation.season, season)
        self.assertEqual(participation.total_scoreable_attempts, 2)
