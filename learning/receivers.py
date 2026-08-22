"""Wiring-only learning event receivers."""

from django.dispatch import receiver

from learning.signals import attempt_registered


@receiver(
    attempt_registered,
    dispatch_uid="learning.progress.on_attempt_registered",
)
def update_progress_on_attempt_registered(sender, attempt, result, **kwargs):
    """Reserve progress reaction wiring for its future owning feature."""
