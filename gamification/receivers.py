"""Wiring-only gamification event receivers."""

from django.dispatch import receiver

from learning.signals import attempt_registered, session_completed


@receiver(
    attempt_registered,
    dispatch_uid="gamification.scoring.on_attempt_registered",
)
def award_score_on_attempt_registered(sender, attempt, result, **kwargs):
    """Reserve scoring reaction wiring for its future owning feature."""


@receiver(
    attempt_registered,
    dispatch_uid="gamification.streaks.on_attempt_registered",
)
def update_streak_on_attempt_registered(sender, attempt, result, **kwargs):
    """Reserve streak reaction wiring for its future owning feature."""


@receiver(
    attempt_registered,
    dispatch_uid="gamification.participation.on_attempt_registered",
)
def update_participation_on_attempt_registered(sender, attempt, result, **kwargs):
    """Reserve attempt participation wiring for its future owning feature."""


@receiver(
    session_completed,
    dispatch_uid="gamification.participation.on_session_completed",
)
def update_participation_on_session_completed(
    sender,
    enrollment,
    completed_at,
    idempotency_key,
    **kwargs,
):
    """Reserve completed-session participation wiring for its future owner."""
