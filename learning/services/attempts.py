"""Stable attempt service contracts and projections."""

from dataclasses import dataclass

from django.db.models import QuerySet

from catalog.models import Choice, ContentVersion
from learning.models import Attempt, Enrollment


@dataclass(frozen=True)
class AttemptResult:
    attempt: Attempt
    rating: str
    is_scoreable: bool
    consequence: str
    explanation: str
    source: str


def register_attempt(
    enrollment: Enrollment,
    content_version: ContentVersion,
    choice: Choice,
    idempotency_key: str,
) -> AttemptResult:
    """Register an answer through a future atomic attempt workflow.

    Preconditions: enrollment, immutable content version, and choice are persisted,
    mutually related, currently eligible, and the caller key is nonempty.
    Result: AttemptResult with server-derived rating, feedback, source, and scoreability.
    Ordering: new attempts follow persistence time then UUID; list_attempts exposes it.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future validation, authorization,
    or integrity failures roll back the attempt and every synchronous receiver write.
    Future authorization: reload the enrollment account and validate current access.
    Idempotency: derive security_digest(idempotency_key, purpose="learning.attempt.idempotency"),
    persist no raw key, return the committed prior result without re-emitting, and allow
    key reuse after a complete rollback.
    """
    raise NotImplementedError


def list_attempts(enrollment: Enrollment) -> QuerySet[Attempt]:
    """Return attempts with their immutable content and choice in stable order."""
    return (
        Attempt.objects.filter(enrollment=enrollment)
        .select_related("content_version", "choice")
        .order_by("attempted_at", "id")
    )
