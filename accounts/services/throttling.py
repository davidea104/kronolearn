"""Database-backed progressive login throttling."""

import math
from contextlib import contextmanager
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import LoginThrottleBucket
from accounts.security import canonicalize_account_email, security_digest

MAX_DELAY_SECONDS = 60
OBSERVATION_WINDOW = timedelta(minutes=15)
PRUNE_BATCH_SIZE = 100


def _account_digest(email: str) -> str:
    return security_digest(
        canonicalize_account_email(email),
        purpose="login-account",
    )


def _origin_digest(origin: str) -> str:
    return security_digest(origin, purpose="login-origin")


def _scope_keys(email: str, origin: str) -> tuple[tuple[str, str], ...]:
    return (
        (LoginThrottleBucket.Scope.ACCOUNT, _account_digest(email)),
        (LoginThrottleBucket.Scope.ORIGIN, _origin_digest(origin)),
    )


def _advisory_lock_id(key_digest: str) -> int:
    lock_id = int(key_digest[:16], 16)
    return lock_id - 2**64 if lock_id >= 2**63 else lock_id


@contextmanager
def serialized_login_attempt(email: str, origin: str):
    """Serialize credential evaluation sharing either account or origin scope."""
    with transaction.atomic():
        if connection.vendor == "postgresql":
            lock_ids = sorted(
                {
                    _advisory_lock_id(key_digest)
                    for _, key_digest in _scope_keys(email, origin)
                }
            )
            with connection.cursor() as cursor:
                for lock_id in lock_ids:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
        yield


def _prune_expired_buckets(current_time) -> None:
    cutoff = current_time - OBSERVATION_WINDOW
    stale_ids = list(
        LoginThrottleBucket.objects.filter(last_failed_at__lte=cutoff)
        .order_by("last_failed_at")
        .values_list("pk", flat=True)[:PRUNE_BATCH_SIZE]
    )
    if stale_ids:
        LoginThrottleBucket.objects.filter(
            pk__in=stale_ids,
            last_failed_at__lte=cutoff,
        ).delete()


def evaluate_login_throttle(
    email: str,
    origin: str,
    *,
    now=None,
) -> int:
    """Return whole retry seconds for the later active account/origin bucket."""
    current_time = now or timezone.now()
    _prune_expired_buckets(current_time)
    expected_keys = _scope_keys(email, origin)
    key_filter = Q()
    for scope, key_digest in expected_keys:
        key_filter |= Q(scope=scope, key_digest=key_digest)
    blocked_until_values = LoginThrottleBucket.objects.filter(key_filter).values_list(
        "scope", "key_digest", "blocked_until"
    )
    expected_keys = set(expected_keys)
    active_until = [
        blocked_until
        for scope, key_digest, blocked_until in blocked_until_values
        if (scope, key_digest) in expected_keys and blocked_until > current_time
    ]
    if not active_until:
        return 0
    return max(1, math.ceil((max(active_until) - current_time).total_seconds()))


def _create_or_lock_bucket(scope: str, key_digest: str, current_time):
    try:
        return (
            LoginThrottleBucket.objects.select_for_update().get(
                scope=scope,
                key_digest=key_digest,
            ),
            False,
        )
    except LoginThrottleBucket.DoesNotExist:
        try:
            with transaction.atomic():
                return (
                    LoginThrottleBucket.objects.create(
                        scope=scope,
                        key_digest=key_digest,
                        failure_count=1,
                        last_failed_at=current_time,
                        blocked_until=current_time,
                    ),
                    True,
                )
        except IntegrityError:
            return (
                LoginThrottleBucket.objects.select_for_update().get(
                    scope=scope,
                    key_digest=key_digest,
                ),
                False,
            )


@transaction.atomic
def record_login_failure(
    email: str,
    origin: str,
    *,
    now=None,
) -> int:
    """Advance both scopes and return the effective progressive delay."""
    current_time = now or timezone.now()
    delays = []
    for scope, key_digest in _scope_keys(email, origin):
        bucket, created = _create_or_lock_bucket(scope, key_digest, current_time)
        if created or current_time - bucket.last_failed_at >= OBSERVATION_WINDOW:
            bucket.failure_count = 1
        else:
            bucket.failure_count += 1
        delay = min(2 ** (bucket.failure_count - 1), MAX_DELAY_SECONDS)
        bucket.last_failed_at = current_time
        bucket.blocked_until = current_time + timedelta(seconds=delay)
        bucket.save(update_fields=("failure_count", "last_failed_at", "blocked_until"))
        delays.append(delay)
    return max(delays)


@transaction.atomic
def record_login_success(email: str) -> None:
    """Clear account-specific failures without erasing origin attack history."""
    LoginThrottleBucket.objects.filter(
        scope=LoginThrottleBucket.Scope.ACCOUNT,
        key_digest=_account_digest(email),
    ).delete()
