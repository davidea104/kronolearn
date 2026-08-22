"""Stable enrollment service contracts."""

from django.core.exceptions import PermissionDenied
from django.db.models import Count, QuerySet

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
    raise NotImplementedError


def get_enrollment(account: Account, track: Track) -> Enrollment | None:
    """Return the unique enrollment for an account and track when present."""
    return Enrollment.objects.filter(account=account, track=track).first()


def list_enrollments(account: Account) -> QuerySet[Enrollment]:
    """Return an active account's enrollments and track module counts."""
    if not Account.objects.filter(pk=account.pk, is_active=True).exists():
        raise PermissionDenied

    return (
        Enrollment.objects.filter(account=account)
        .select_related("track")
        .annotate(module_count=Count("track__modules"))
        .order_by("enrolled_at", "id")
    )
