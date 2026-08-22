"""Stable daily-session service contracts."""

from catalog.models import ContentVersion
from learning.models import Enrollment


def get_next_content_version(enrollment: Enrollment) -> ContentVersion | None:
    """Resolve the next published content snapshot for a future daily session.

    Preconditions: the enrollment is persisted and eligible for session access.
    Result: the next ContentVersion, or None when no published content remains.
    Ordering: consume catalog.services.content publication order without model queries.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future workflow rejects an
    invalid or inaccessible enrollment before selecting content.
    Future authorization: derive access from the enrollment's current persisted account.
    Idempotency: this is a read; repeated calls over unchanged state return the same row.
    """
    raise NotImplementedError


def is_track_completed(enrollment: Enrollment) -> bool:
    """Report completion from authoritative published content and progress.

    Preconditions: the enrollment is persisted and eligible for progress access.
    Result: True only when all required currently published content is complete.
    Ordering: published content is evaluated in catalog service order.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future workflow rejects an
    invalid or inaccessible enrollment before evaluating completion.
    Future authorization: derive access from the enrollment's current persisted account.
    Idempotency: this is a read; repeated calls over unchanged state return the same bool.
    """
    raise NotImplementedError
