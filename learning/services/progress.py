"""Stable learning-progress service contracts and projections."""

from dataclasses import dataclass
from decimal import Decimal

from learning.models import Enrollment, Progress


@dataclass(frozen=True)
class TrackProgress:
    percentage: Decimal
    modules: tuple[Progress, ...]
    accuracy: Decimal | None

    def __post_init__(self):
        if not Decimal(0) <= self.percentage <= Decimal(100):
            raise ValueError("percentage must be between 0 and 100")


def recompute_progress(enrollment: Enrollment) -> None:
    """Recompute module aggregates in a future atomic progress workflow.

    Preconditions: the enrollment is persisted and its published content and valid
    attempts can be read through their authoritative contracts.
    Result: None after replacing stored Progress values with derived aggregates.
    Ordering: process and persist module aggregates in module position order.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future invalid relationships or
    integrity failures roll back every aggregate update.
    Future authorization: invoked by the owning progress receiver or an authorized
    server-side workflow, never from untrusted actor state.
    Idempotency: recomputing unchanged authoritative facts produces the same aggregates.
    """
    raise NotImplementedError


def get_track_progress(enrollment: Enrollment) -> TrackProgress:
    """Project track progress in a future privacy-preserving read workflow.

    Preconditions: the enrollment is persisted and eligible for progress access.
    Result: TrackProgress with bounded percentage and None accuracy when no scoreable
    attempts exist.
    Ordering: the Progress tuple follows module position.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future read rejects an invalid
    or inaccessible enrollment before returning data.
    Future authorization: derive access from the enrollment's current persisted account.
    Idempotency: this is a read; repeated calls over unchanged state are equivalent.
    """
    raise NotImplementedError
