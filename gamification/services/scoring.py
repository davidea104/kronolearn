"""Stable score-event service contracts."""

from collections.abc import Mapping
from types import MappingProxyType

from catalog.models import Choice
from gamification.models import ScoreEvent
from learning.models import Attempt

RATING_POINTS: Mapping[str, int] = MappingProxyType(
    {
        Choice.Rating.OPTIMAL: 100,
        Choice.Rating.PARTIAL: 50,
        Choice.Rating.INCORRECT: 0,
    }
)


def award_for_attempt(attempt: Attempt) -> ScoreEvent | None:
    """Award at most one score event in a future atomic receiver workflow.

    Preconditions: the persisted attempt has authoritative rating and scoreability.
    Result: one attempt ScoreEvent with base points plus bounded streak bonus, or None
    when the attempt is not scoreable.
    Ordering: not applicable to this singular result; leaderboard owns ranking order.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future invalid relationships or
    integrity failures propagate so the producer transaction rolls back.
    Future authorization: receiver-owned system behavior; no caller-supplied actor is
    trusted or authorized by this function.
    Idempotency: use security_digest(str(attempt.id),
    purpose="gamification.score-event.idempotency"); uniqueness returns the existing
    logical award and prevents a second event for the attempt.
    """
    raise NotImplementedError
