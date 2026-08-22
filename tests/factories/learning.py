"""Deterministic factories for learning entities."""

from accounts.security import security_digest
from learning.models import Attempt, Enrollment, Progress
from tests.factories.accounts import account_factory
from tests.factories.catalog import (
    choice_factory,
    content_item_factory,
    content_version_factory,
    module_factory,
    track_factory,
)


def enrollment_factory(**overrides) -> Enrollment:
    account = overrides.pop("account", None) or account_factory()
    track = overrides.pop("track", None) or track_factory()
    enrollment, _ = Enrollment.objects.get_or_create(
        account=account,
        track=track,
        defaults=overrides,
    )
    return enrollment


def attempt_factory(**overrides) -> Attempt:
    enrollment = overrides.pop("enrollment", None) or enrollment_factory()
    content_version = overrides.pop("content_version", None)
    if content_version is None:
        module = module_factory(track=enrollment.track)
        content_version = content_version_factory(
            content_item=content_item_factory(module=module)
        )
    choice = overrides.pop("choice", None) or choice_factory(
        content_version=content_version
    )
    digest = overrides.pop(
        "idempotency_digest",
        security_digest("factory-attempt", purpose="learning.attempt.idempotency"),
    )
    defaults = {
        "enrollment": enrollment,
        "content_version": content_version,
        "choice": choice,
        "rating": choice.rating,
        **overrides,
    }
    attempt, _ = Attempt.objects.get_or_create(
        idempotency_digest=digest, defaults=defaults
    )
    return attempt


def progress_factory(**overrides) -> Progress:
    enrollment = overrides.pop("enrollment", None) or enrollment_factory()
    module = overrides.pop("module", None) or module_factory(track=enrollment.track)
    defaults = {
        "completed_items": 0,
        "total_items": 0,
        "correct_attempts": 0,
        **overrides,
    }
    progress, _ = Progress.objects.get_or_create(
        enrollment=enrollment, module=module, defaults=defaults
    )
    return progress
