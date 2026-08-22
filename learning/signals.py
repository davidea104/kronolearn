"""Public synchronous domain-event contracts owned by learning."""

from django.dispatch import Signal

attempt_registered = Signal()
session_completed = Signal()
