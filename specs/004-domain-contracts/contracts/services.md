# Service Contracts

All paths and signatures in this document are stable public interfaces. Parameters are positional unless shown with a default. STUB functions raise `NotImplementedError` immediately and perform no read or write. Feature 004 verifies the documented canonical digest inputs and purposes through contract/docstring inspection and direct determinism and purpose-separation tests of `accounts.security.security_digest`; runtime producer integration belongs to the features that implement the STUBs.

## Shared Types

```python
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeAlias

MetricNumber: TypeAlias = int | float | Decimal


@dataclass(frozen=True)
class AttemptResult:
    attempt: Attempt
    rating: str
    is_scoreable: bool
    consequence: str
    explanation: str
    source: str


@dataclass(frozen=True)
class TrackProgress:
    percentage: Decimal
    modules: tuple[Progress, ...]
    accuracy: Decimal | None


@dataclass(frozen=True)
class LeaderboardEntry:
    display_name: str
    position: int
    weekly_points: int
    correct_scoreable_attempts: int
    total_scoreable_attempts: int
    completed_sessions: int


@dataclass(frozen=True)
class ContentMetrics:
    context: str
    person_count: int
    is_suppressed: bool
    values: Mapping[str, MetricNumber]


@dataclass(frozen=True)
class EngagementMetrics:
    context: str
    person_count: int
    is_suppressed: bool
    values: Mapping[str, MetricNumber]
```

Metric mappings are copied into `MappingProxyType`. `values` is empty whenever `is_suppressed` is true. No projection contains email or an internal account identifier.

## Catalog

Module: `catalog.services.content`

```python
def publish_content_item(
    content_item: ContentItem,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentVersion: ...  # STUB


def create_content_draft(
    module: Module,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentItem: ...  # STUB


def get_published_version(
    content_item: ContentItem,
) -> ContentVersion | None: ...  # IMPLEMENT


def list_published_versions(track: Track) -> list[ContentVersion]: ...  # IMPLEMENT
```

- `get_published_version` returns the row whose version number equals the item's `published_version`; it returns `None` for draft/unpublished/missing-current states and never falls back to another number.
- `list_published_versions` includes only published items under active modules of the supplied track and returns current versions ordered by module position, item position, then stable UUID.
- Future mutations derive authorization from the current persisted actor and validate revision under lock.

## Learning Enrollment

Module: `learning.services.enrollment`

```python
def enroll(account: Account, track: Track) -> Enrollment: ...  # STUB


def get_enrollment(
    account: Account,
    track: Track,
) -> Enrollment | None: ...  # IMPLEMENT


def list_enrollments(account: Account) -> QuerySet[Enrollment]: ...  # IMPLEMENT
```

`list_enrollments` orders by `enrolled_at`, then UUID, and eager-loads the track. It returns all statuses; filtering active enrollments is a future workflow rule.

## Learning Session

Module: `learning.services.session`

```python
def get_next_content_version(
    enrollment: Enrollment,
) -> ContentVersion | None: ...  # STUB


def is_track_completed(enrollment: Enrollment) -> bool: ...  # STUB
```

The future implementation reads published catalog content through `catalog.services.content` and never imports catalog models for queries.

## Learning Attempts

Module: `learning.services.attempts`

```python
def register_attempt(
    enrollment: Enrollment,
    content_version: ContentVersion,
    choice: Choice,
    idempotency_key: str,
) -> AttemptResult: ...  # STUB


def list_attempts(enrollment: Enrollment) -> QuerySet[Attempt]: ...  # IMPLEMENT
```

`list_attempts` orders by `attempted_at`, then UUID, and eager-loads content version and choice. Future registration derives `security_digest(idempotency_key, purpose="learning.attempt.idempotency")`, derives rating and feedback server-side, and emits the event defined in [domain-events.md](domain-events.md). The raw key is neither persisted nor placed in the event.

## Learning Progress

Module: `learning.services.progress`

```python
def recompute_progress(enrollment: Enrollment) -> None: ...  # STUB


def get_track_progress(enrollment: Enrollment) -> TrackProgress: ...  # STUB
```

For an enrollment with no published content, percentage is `0`; with no scoreable attempts, accuracy is `None`. Module projections follow module position.

## Gamification Scoring

Module: `gamification.services.scoring`

```python
RATING_POINTS: Mapping[str, int] = MappingProxyType(
    {
        Choice.Rating.OPTIMAL: 100,
        Choice.Rating.PARTIAL: 50,
        Choice.Rating.INCORRECT: 0,
    }
)


def award_for_attempt(attempt: Attempt) -> ScoreEvent | None: ...  # STUB
```

The future function returns one event with cause `attempt` and amount equal to base points plus bounded streak bonus, or `None` when the attempt is not scoreable. Its digest is `security_digest(str(attempt.id), purpose="gamification.score-event.idempotency")`.

## Gamification Streaks

Module: `gamification.services.streaks`

```python
STREAK_BONUS_STEP = 10
STREAK_BONUS_CAP = 50


def register_activity(account: Account, activity_date: date) -> Streak: ...  # STUB


def streak_bonus(streak: Streak) -> int: ...  # STUB
```

Dates are project-calendar dates. Future implementations do not accept browser timezone input.

## Gamification Seasons

Module: `gamification.services.seasons`

```python
def current_season(moment: datetime) -> WeeklySeason: ...  # IMPLEMENT


def leaderboard(season: WeeklySeason) -> list[LeaderboardEntry]: ...  # STUB
```

`current_season` accepts aware datetimes, converts them to the project timezone, derives Monday through Sunday, and atomically returns the unique row. Naive datetimes are rejected. Concurrent unique conflicts are resolved by fetching the winning row.

## Analytics Metrics

Module: `analytics.services.metrics`

```python
def content_metrics(track: Track | None = None) -> ContentMetrics: ...  # STUB


def engagement_metrics(window_days: int) -> EngagementMetrics: ...  # STUB
```

`window_days` must be positive in the future implementation. `context` is a public textual scope, not an account identifier. Metric names and units are documented when the implementing feature adds each key.
