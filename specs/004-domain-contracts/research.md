# Phase 0 Research: Contratos y esqueleto de dominio

**Date**: 2026-08-21  
**Spec**: [spec.md](spec.md)  
**Plan**: [plan.md](plan.md)

All technical questions are resolved. The decisions below provide the choices needed for Phase 1.

## 1. Domain ownership and migration boundaries

**Decision**: Keep each persistent entity in its owning Django app: content in `catalog`, enrollment/attempt/progress in `learning`, and score/streak/season in `gamification`. Create exactly one new migration in each of those apps; do not migrate `accounts` or `analytics`.

**Rationale**: This follows the existing modular monolith, lets each app own its write invariants, and gives the six parallel features a single migration baseline. `Account.display_name` already exists, while analytics requires projections rather than storage.

**Alternatives considered**:

- A new shared `domain` app: rejected because it erases app ownership and centralizes unrelated write rules.
- Put all new entities in `learning`: rejected because content and gamification have separate owners.
- Let later features add their own migrations: rejected because avoiding divergent migrations is the feature's primary purpose.

## 2. Published content and current-version resolution

**Decision**: Store `published_version` on `ContentItem` and expose `ContentVersion.is_current` as a read-only derived property comparing version numbers. Reuse `catalog.models.ImmutableModel` for `ContentVersion`, `Choice`, and `LabExercise`.

**Rationale**: Publication changes one mutable aggregate root without mutating historical snapshots. This matches the existing `Track`/`TrackVersion` and `Module`/`ModuleVersion` pattern.

**Alternatives considered**:

- Mutable `is_current` column on every version: rejected because publishing would mutate an old snapshot.
- Foreign key from item to current version: rejected because it introduces a circular migration/state dependency and differs from the established catalog pattern.

## 3. Idempotency-key privacy and uniqueness

**Decision**: Reuse `accounts.security.security_digest`. The future attempt producer hashes the complete opaque key with purpose `learning.attempt.idempotency`; the future attempt score-event producer hashes the canonical `str(attempt.id)` with purpose `gamification.score-event.idempotency`. Only the globally unique 64-character digest persists. Feature 004 verifies the exact inputs and purposes in contracts/docstrings and directly tests helper determinism and purpose separation; runtime producer integration remains with the implementing features.

**Rationale**: The existing helper derives an HMAC-SHA256 key from `SECRET_KEY` and the fixed purpose. A unique database constraint is the concurrency guarantee, digest-only storage avoids persisting client tokens, and stable purpose separation prevents cross-domain correlation without introducing another secret.

**Alternatives considered**:

- Store the raw key in a unique column: rejected because it persists a client-controlled token.
- Check for an existing row before insert without uniqueness: rejected because it races under concurrency.
- UUID-only keys: rejected because the public contract intentionally accepts opaque caller keys.
- Add domain IDs to the attempt input: rejected because the public idempotency key is already globally unique and must retain the same meaning across retries.
- Invoke or partially implement STUB producers to verify digest use: rejected because it would violate the feature boundary and give placeholder code observable behavior.

## 4. Set-level Choice publication rules

**Decision**: Enforce per-row position bounds and uniqueness in database constraints. Treat consecutive content positions and “three or four choices, consecutive positions, at least one optimal” as aggregate preconditions of their future owning services. Those services lock the parent and candidate rows when implemented. This feature creates valid factories/demo data and contract tests but leaves those mutations as STUBs.

**Rationale**: Standard row checks cannot count sibling rows or assert that one sibling has a particular rating. The owning service is the correct boundary for this aggregate invariant.

**Alternatives considered**:

- Database trigger: rejected because it adds hidden, vendor-specific business behavior and complicates SQLite compatibility.
- Validation in forms: rejected because imports and direct service use would bypass it.
- Validate in `Choice.save()`: rejected because individual saves cannot determine when the set is complete.

## 5. WeeklySeason canonical dates and non-overlap

**Decision**: `current_season(moment)` is the public creation path: it converts the moment to `America/Bogota`, derives Monday and Sunday dates, and creates the canonical row atomically. Portable checks enforce ordered dates and uniqueness. The gamification migration conditionally adds a PostgreSQL GiST exclusion constraint over `daterange(starts_on, ends_on, '[]')`; SQLite skips only that database operation.

**Rationale**: Canonical construction handles ordinary use, while PostgreSQL must reject any overlapping row even under direct or concurrent writes. The constitution explicitly makes PostgreSQL the acceptance authority for migrations and concurrency.

**Alternatives considered**:

- Service validation only: rejected because direct or concurrent writes could violate non-overlap.
- PostgreSQL range field as the model's only representation: rejected because the full model must also migrate and run under SQLite.
- Treat unique Monday start dates as sufficient: rejected because malformed manually inserted ranges could still overlap.

## 6. Synchronous domain-event delivery

**Decision**: Define `attempt_registered = Signal()` and `session_completed = Signal()`. The future producers use `Signal.send()`, not `send_robust()`, inside their atomic blocks. Attempt receivers accept `sender`, `attempt`, `result`, and `**kwargs`; session receivers accept `sender`, `enrollment`, `completed_at`, `idempotency_key`, and `**kwargs`. Each app registers once only the events it consumes: `learning` subscribes its progress hook to `attempt_registered`; `gamification` subscribes scoring, streak, and participation hooks to `attempt_registered` and its participation hook to `session_completed`. Each receiver uses a stable `dispatch_uid` from its own `AppConfig.ready()` import. Feature 004 verifies each envelope, synchronous ordering, exception propagation, rollback, and duplicate registration through an explicit transactional harness; producer creation, replay, and retry tests remain with the later producer features.

**Rationale**: Django dispatches `send()` synchronously and propagates receiver exceptions, producing all-or-nothing rollback without implementing either STUB producer. `dispatch_uid` prevents duplicate registration when `ready()` runs multiple times in tests. `gamification` remains the sole writer of `SeasonParticipation`: future receivers consume attempt activity for points/attempt counters and completed-session activity for the session counter. `ScoreEvent` persistence keeps generic constraints and accepts a `session_completed` row with amount zero and no attempt; the future session receiver, rather than a cause-specific database check, guarantees that semantic combination.

**Alternatives considered**:

- `send_robust()`: rejected because it catches receiver exceptions and would permit partial success.
- `transaction.on_commit()`: rejected because effects would run outside the attempt transaction.
- Direct service calls: rejected because they couple the attempt producer to progress and gamification.
- End-to-end producer tests in this feature: rejected because both functional producers remain STUBs.

**Reference**: Django 5.2, [Signals](https://docs.djangoproject.com/en/5.2/topics/signals/), especially `Signal.send()`, exception behavior, `ready()`, and `dispatch_uid`.

## 7. Stable Python service contracts

**Decision**: Use module-level typed functions and frozen dataclasses, matching existing services. Query-returning contracts use `QuerySet[Model]`; collection projections use tuples; metric maps are exposed as read-only mappings. STUBs validate no domain input and raise `NotImplementedError` immediately so they cannot create side effects.

**Rationale**: This preserves import paths and return shapes while leaving business rules to later owners. Frozen dataclasses make event payloads and projections safe to share.

**Alternatives considered**:

- Service classes: rejected because the repository uses module-level functions and no dependency-injection container.
- Untyped dictionaries: rejected because keys can drift without contract tests.
- Placeholder return values such as `None`: rejected because callers could mistake a stub for implemented behavior.

## 8. Navigation and URL discovery

**Decision**: Each app declares immutable `NAV_ITEMS` in `nav.py`. `ui.navigation` iterates installed apps, imports optional nav modules, sorts entries deterministically, and excludes entries whose named URL cannot yet be reversed. A context processor exposes the resolved entries. Root composition includes each app once; `learning.urls` is a package that includes four area modules.

**Rationale**: Future route modules become visible automatically when their names resolve, without editing the base template or a central list. Missing future routes do not break current rendering.

**Alternatives considered**:

- Hard-coded links in `base.html`: rejected because every feature would edit one shared file.
- A central editable registry: rejected because it remains a merge-conflict hotspot.
- Database-backed navigation: rejected because navigation metadata does not require runtime administration.

## 9. Backward-compatible base template blocks

**Decision**: Add stable blocks `main`, `sidebar`, `fragments`, and `scripts`; retain `title`; nest the existing `content` block inside `main` during the compatibility period. Preserve semantic navigation and visible keyboard focus, verified with fast automated assertions over rendered HTML and applicable style rules rather than browser automation or manual review.

**Rationale**: Existing templates override `content`. Removing it would break current catalog/account pages, while nesting allows new features to target `main` without changing old templates.

**Alternatives considered**:

- Rename `content` directly to `main`: rejected because it is a breaking change.
- Keep only `content`: rejected because it does not fulfill the frozen block contract.
- Add browser automation for this structural contract: rejected because rendered-template and style assertions provide faster deterministic evidence without a new dependency.

## 10. Demo-data orchestration

**Decision**: Expose `seed_demo` as a composition-layer management command under `ui`. Wrap the complete seed in one transaction and use stable natural keys plus `get_or_create`/locked updates. Demo accounts use deterministic, non-personal addresses under the reserved `.invalid` domain as their private `Account` natural keys. Require `--confirm-production` whenever `DEBUG` is false; create unusable passwords in that mode and never expose emails or credentials in output, logs, events, audit, metrics, or rankings.

**Rationale**: The command intentionally coordinates all apps and does not represent domain reaction logic. Django management commands provide testable `stdout`/`stderr`, argument parsing, and `CommandError` for refusal.

**Alternatives considered**:

- Data migration: rejected because demo data is optional and environment-sensitive.
- Fixture JSON: rejected because cross-model natural-key repair and current-week creation need controlled idempotency.
- Put orchestration in a domain service: rejected because no single domain app owns the demo scenario.

**Reference**: Django 5.2, [custom management commands](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/).

## 11. Factories without a new dependency

**Decision**: Implement small typed factory functions under `tests/factories/` using Django's ORM and deterministic sequence helpers. Import factories from their owning module; keep `tests/factories/__init__.py` empty.

**Rationale**: The project has no factory library and this feature does not justify another dependency. Direct module imports also avoid a shared re-export file becoming a merge hotspot.

**Alternatives considered**:

- Add Factory Boy: rejected because the required factory surface is small and dependency growth is prohibited without need.
- One large `tests/factories.py`: rejected because parallel features would edit the same file.

## 12. Dual-backend verification

**Decision**: Add an explicit SQLite contract step using `kronolearn.settings.test`, then run migrations and the full suite with the existing PostgreSQL CI environment. Tag or group PostgreSQL-only migration, exclusion, concurrency, and audit cases so they are explicit acceptance gates rather than silently skipped evidence.

**Rationale**: SQLite catches portable model/query regressions quickly, but it cannot establish PostgreSQL locking or exclusion behavior. Both are required, with PostgreSQL authoritative for critical guarantees.

**Alternatives considered**:

- SQLite only: rejected by the constitution and feature requirements.
- PostgreSQL only: rejected because the feature explicitly requires the fast SQLite suite to remain usable.
- Make backend-specific tests pass by weakening constraints: rejected because portability cannot override integrity.

## 13. Documentation drift prevention

**Decision**: During planning, `spec.md` and the Phase 1 contract artifacts are the approved design inputs. During implementation, code must conform to them. At feature completion, `docs/contracts/domain-contracts.md` becomes the single human source of truth; automated drift tests compare its public symbol names, result fields, event envelopes, route namespaces, blocks, six baseline ownership assignments, and five backlog traces with executable artifacts.

**Rationale**: Stable contracts are the product of this feature; undocumented drift would block or mislead parallel teams even if runtime tests pass.

**Alternatives considered**:

- Rely on code docstrings alone: rejected because they cannot express the cross-app entity diagram and ownership table.
- Generate all documentation from reflection: rejected because transaction semantics, rationale, and ownership are not fully derivable from code.
- Require timed human reviewers as acceptance evidence: rejected because deterministic automated ownership and traceability checks are faster and repeatable in CI.
