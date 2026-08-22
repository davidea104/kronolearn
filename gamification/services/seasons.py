"""Canonical weekly-season services and public leaderboard projections."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from gamification.models import WeeklySeason


@dataclass(frozen=True)
class LeaderboardEntry:
    display_name: str
    position: int
    weekly_points: int
    correct_scoreable_attempts: int
    total_scoreable_attempts: int
    completed_sessions: int


def current_season(moment: datetime) -> WeeklySeason:
    """Atomically return the Monday-Sunday season for an aware project instant."""
    if timezone.is_naive(moment):
        raise ValueError("moment must be timezone-aware")
    project_date = timezone.localtime(moment).date()
    starts_on = project_date - timedelta(days=project_date.weekday())
    ends_on = starts_on + timedelta(days=6)
    try:
        with transaction.atomic():
            season, _ = WeeklySeason.objects.get_or_create(
                starts_on=starts_on,
                defaults={"ends_on": ends_on},
            )
            return season
    except IntegrityError:
        return WeeklySeason.objects.get(starts_on=starts_on, ends_on=ends_on)


def leaderboard(season: WeeklySeason) -> list[LeaderboardEntry]:
    """Return a future privacy-preserving weekly ranking.

    Preconditions: season is persisted and eligible for ranking publication.
    Result: LeaderboardEntry values with public display names and no account identifiers.
    Ordering: entries are ordered by ascending position with deterministic tie-breaking.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future read rejects an invalid or
    inaccessible season before returning data.
    Future authorization: the owning view enforces current server-side ranking access.
    Idempotency: this is a read; repeated calls over unchanged state are equivalent.
    """
    raise NotImplementedError
