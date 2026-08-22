"""Stable streak service contracts."""

from datetime import date

from accounts.models import Account
from gamification.models import Streak

STREAK_BONUS_STEP = 10
STREAK_BONUS_CAP = 50


def register_activity(account: Account, activity_date: date) -> Streak:
    """Register activity in a future atomic streak workflow.

    Preconditions: the account is persisted and activity_date is a project-calendar
    date derived server-side rather than supplied as browser-local time.
    Result: the account's Streak updated for the qualifying activity date.
    Ordering: dates advance chronologically; older or same-day activity cannot skip days.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future invalid dates or integrity
    failures propagate so the producer transaction rolls back.
    Future authorization: receiver-owned system behavior uses the attempt's account,
    never a caller-selected account identity.
    Idempotency: repeated qualifying activity on the same project date does not advance
    the streak more than once.
    """
    raise NotImplementedError


def streak_bonus(streak: Streak) -> int:
    """Calculate a future bounded bonus from persisted streak state.

    Preconditions: streak is a persisted, valid nonnegative Streak aggregate.
    Result: an integer from zero through STREAK_BONUS_CAP in STREAK_BONUS_STEP steps.
    Ordering: not applicable to this scalar projection.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future calculation rejects
    invalid streak state rather than returning an out-of-range bonus.
    Future authorization: not applicable; callers authorize access to the Streak before
    invoking this pure domain calculation.
    Idempotency: the calculation is pure for unchanged streak state.
    """
    raise NotImplementedError
