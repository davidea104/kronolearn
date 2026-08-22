"""Gamification persistence contracts."""

import uuid
from typing import ClassVar

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models import F, Func, Q, Value

from catalog.models import ImmutableModel


class ScoreEvent(ImmutableModel):
    """Append-only idempotent scoring fact."""

    class Cause(models.TextChoices):
        ATTEMPT = "attempt", "Attempt"
        SESSION_COMPLETED = "session_completed", "Session completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cause = models.CharField(max_length=64)
    amount = models.PositiveIntegerField()
    attempt = models.OneToOneField(
        "learning.Attempt",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="score_event",
    )
    occurred_at = models.DateTimeField(auto_now_add=True)
    idempotency_digest = models.CharField(max_length=64, unique=True, editable=False)

    class Meta:
        default_permissions = ("view",)
        ordering = ("occurred_at", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=~Q(cause="attempt") | Q(attempt__isnull=False),
                name="gamification_score_attempt_required",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("cause", "occurred_at"),
                name="gamification_score_cause_idx",
            ),
        ]


class Streak(models.Model):
    """Current and longest activity streak for one account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="streak",
    )
    current_length = models.PositiveIntegerField(default=0)
    longest_length = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(longest_length__gte=F("current_length")),
                name="gamification_streak_longest_gte_current",
            ),
        ]


class WeeklySeason(models.Model):
    """Canonical non-overlapping project week."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    starts_on = models.DateField(unique=True)
    ends_on = models.DateField(unique=True)

    class Meta:
        ordering = ("-starts_on", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(starts_on__lte=F("ends_on")),
                name="gamification_season_dates_ordered",
            ),
            ExclusionConstraint(
                name="gamification_season_no_overlap",
                expressions=(
                    (
                        Func(
                            F("starts_on"),
                            F("ends_on"),
                            Value("[]"),
                            function="DATERANGE",
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ),
            ),
        ]


class SeasonParticipation(models.Model):
    """Weekly ranking aggregate for one account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    season = models.ForeignKey(
        WeeklySeason, on_delete=models.PROTECT, related_name="participations"
    )
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="season_participations",
    )
    weekly_points = models.PositiveIntegerField(default=0)
    correct_scoreable_attempts = models.PositiveIntegerField(default=0)
    total_scoreable_attempts = models.PositiveIntegerField(default=0)
    completed_sessions = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-weekly_points", "account__display_name", "account_id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("season", "account"),
                name="gamification_participation_unique",
            ),
            models.CheckConstraint(
                condition=Q(
                    correct_scoreable_attempts__lte=F("total_scoreable_attempts")
                ),
                name="gamification_participation_correct_lte_total",
            ),
        ]
