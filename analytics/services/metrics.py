"""Privacy-preserving analytics service contracts and projections."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import TypeAlias

from catalog.models import Track

MetricNumber: TypeAlias = int | float | Decimal


@dataclass(frozen=True)
class ContentMetrics:
    context: str
    person_count: int
    is_suppressed: bool
    values: Mapping[str, MetricNumber]

    def __post_init__(self):
        values = {} if self.is_suppressed else dict(self.values)
        object.__setattr__(self, "values", MappingProxyType(values))


@dataclass(frozen=True)
class EngagementMetrics:
    context: str
    person_count: int
    is_suppressed: bool
    values: Mapping[str, MetricNumber]

    def __post_init__(self):
        values = {} if self.is_suppressed else dict(self.values)
        object.__setattr__(self, "values", MappingProxyType(values))


def content_metrics(track: Track | None = None) -> ContentMetrics:
    """Return future aggregate content metrics with cohort suppression.

    Preconditions: track is None or a persisted Track and a configurable privacy
    threshold has been defined by the implementing feature.
    Result: ContentMetrics for the public scope with empty values when suppressed.
    Ordering: metric mappings have no semantic key order.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; future invalid scope or access fails
    before any aggregate is returned.
    Future authorization: the owning administrative view validates current server-side
    analytics access; no account identifier enters the projection.
    Idempotency: this is a read; repeated calls over unchanged state are equivalent.
    """
    raise NotImplementedError


def engagement_metrics(window_days: int) -> EngagementMetrics:
    """Return future aggregate engagement metrics with cohort suppression.

    Preconditions: window_days is positive and a configurable privacy threshold has
    been defined by the implementing feature.
    Result: EngagementMetrics for the public window with empty values when suppressed.
    Ordering: metric mappings have no semantic key order.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future implementation rejects a
    nonpositive window or unauthorized access before returning an aggregate.
    Future authorization: the owning administrative view validates current server-side
    analytics access; no account identifier enters the projection.
    Idempotency: this is a read; repeated calls over unchanged state are equivalent.
    """
    raise NotImplementedError
