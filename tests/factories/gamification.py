"""Deterministic factories for gamification entities."""

from datetime import timedelta

from django.utils import timezone

from accounts.security import security_digest
from gamification.models import ScoreEvent, SeasonParticipation, Streak, WeeklySeason
from tests.factories.accounts import account_factory
from tests.factories.learning import attempt_factory


def score_event_factory(**overrides) -> ScoreEvent:
    attempt = overrides.pop("attempt", None) or attempt_factory()
    digest = overrides.pop(
        "idempotency_digest",
        security_digest(
            str(attempt.id), purpose="gamification.score-event.idempotency"
        ),
    )
    defaults = {
        "cause": ScoreEvent.Cause.ATTEMPT,
        "amount": 100,
        "attempt": attempt,
        **overrides,
    }
    event, _ = ScoreEvent.objects.get_or_create(
        idempotency_digest=digest, defaults=defaults
    )
    return event


def streak_factory(**overrides) -> Streak:
    account = overrides.pop("account", None) or account_factory()
    defaults = {
        "current_length": 0,
        "longest_length": 0,
        "last_activity_date": None,
        **overrides,
    }
    streak, _ = Streak.objects.get_or_create(account=account, defaults=defaults)
    return streak


def weekly_season_factory(**overrides) -> WeeklySeason:
    today = timezone.localdate()
    starts_on = overrides.pop("starts_on", today - timedelta(days=today.weekday()))
    defaults = {"ends_on": starts_on + timedelta(days=6), **overrides}
    season, _ = WeeklySeason.objects.get_or_create(
        starts_on=starts_on, defaults=defaults
    )
    return season


def season_participation_factory(**overrides) -> SeasonParticipation:
    season = overrides.pop("season", None) or weekly_season_factory()
    account = overrides.pop("account", None) or account_factory()
    defaults = {
        "weekly_points": 0,
        "correct_scoreable_attempts": 0,
        "total_scoreable_attempts": 0,
        "completed_sessions": 0,
        **overrides,
    }
    participation, _ = SeasonParticipation.objects.get_or_create(
        season=season, account=account, defaults=defaults
    )
    return participation
