"""Stable enrollment service contracts."""

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from accounts.models import Account
from catalog.models import Track
from learning.models import Enrollment


def enroll(account: Account, track: Track) -> Enrollment:
    """Enroll an account in a track through a future atomic workflow.

    Preconditions: the persisted account is eligible and the persisted track can be
    enrolled in under the future workflow rules.
    Result: the unique active Enrollment for the account and track.
    Ordering: not applicable to this singular result; list_enrollments defines listing.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future invalid or unauthorized
    requests fail atomically without creating a partial enrollment.
    Future authorization: reload the account and evaluate current server-side state.
    Idempotency: repeated calls for the same account and track return the same logical
    enrollment rather than creating a duplicate.
    """
    # Attempt to create the unique enrollment. If a concurrent or prior create
    # violates the unique constraint, return the existing enrollment instead
    # of raising so callers can assume idempotent behavior.
    try:
        with transaction.atomic():
            return Enrollment.objects.create(account=account, track=track)
    except IntegrityError as exc:
        # The UniqueConstraint in the model uses name learning_enrollment_account_track_unique
        # We don't inspect the message; simply return the existing enrollment when
        # creation failed due to uniqueness.
        existing = get_enrollment(account, track)
        if existing is not None:
            return existing
        # If no existing row found, re-raise the original exception since
        # something else went wrong.
        raise


def get_enrollment(account: Account, track: Track) -> Enrollment | None:
    """Return the unique enrollment for an account and track when present."""
    return Enrollment.objects.filter(account=account, track=track).first()


def list_enrollments(account: Account) -> QuerySet[Enrollment]:
    """Return all account enrollments with tracks loaded in stable order."""
    return (
        Enrollment.objects.filter(account=account)
        .select_related("track")
        .order_by("enrolled_at", "id")
    )
