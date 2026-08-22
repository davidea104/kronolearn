# Implementation Plan: Contratos y esqueleto de dominio

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking in `tasks.md`, generated separately by `/speckit-tasks`.

**Branch**: `004-domain-contracts` | **Date**: 2026-08-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-domain-contracts/spec.md`

## Summary

Create the complete shared domain schema and stable internal contracts needed by six parallel baseline features and five backlog features without delivering user-facing workflows. The design extends the existing modular Django monolith with app-owned models and migrations, typed service stubs and read-only implementations, two synchronous transactional domain-event envelopes, prewired URL/template/navigation extension points, deterministic demo data, reusable factories, and PostgreSQL-backed integrity evidence.

The feature is intentionally one coordinated plan: splitting schema, contracts, and composition across separate plans would recreate the migration and merge conflicts this work exists to prevent. Implementation tasks must still be independently testable and grouped by owning app.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, psycopg 3.3.4, Ruff 0.16.3; no new runtime dependency

**Storage**: PostgreSQL 16 as the authoritative acceptance database; SQLite in-memory as a fast supplementary test backend

**Testing**: Django `TestCase` and `TransactionTestCase` through `python manage.py test`; `unittest.mock` for contract isolation; fast rendered-HTML and style/class assertions for accessibility; direct `security_digest` tests; `ThreadPoolExecutor` plus separate connections for PostgreSQL concurrency cases; Ruff for lint and formatting

**Target Platform**: Linux deployment on Railway and local Windows/Linux development

**Project Type**: Server-rendered modular Django web application

**Performance Goals**: A clean demo seed completes in under 2 minutes; implemented read queries use bounded eager loading and deterministic indexed ordering; no request-throughput target applies because this feature adds no functional endpoint

**Constraints**: No new infrastructure or dependency; no visible learner/admin workflow; published snapshots are append-only; idempotency is database-backed; domain-event receivers execute synchronously in one transaction; accessibility acceptance uses fast automated structural tests without browser or manual review; account identity is never exposed by metrics or ranking; project calendar uses `America/Bogota`; all critical database evidence runs on PostgreSQL

**Scale/Scope**: 11 new persistent entities across three owning apps, 20 public service functions, five immutable result types, two domain signals, four root URL namespaces, seven reserved template and test areas, six parallel baseline consumers, and five backlog consumers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Evidence in this plan | Status |
| --- | --- | --- |
| 1. Desarrollo guiado por especificaciones | Approved spec and quality checklist exist before planning; feature requirements reference constitutional rules and add only feature-specific manifestations. | PASS |
| 2. Autoridad del dominio | Mutations remain STUBs in named service modules; views and templates receive no domain logic. | PASS |
| 3. Contenido administrado como datos | Content, choices, and labs are modeled data with immutable published snapshots. | PASS |
| 4. Seguridad por defecto | No new endpoint accepts account identity; demo execution is gated outside development. | PASS |
| 5. Idempotencia e integridad | Attempt and ScoreEvent store unique HMAC digests with fixed purposes; contracts/docstrings and direct helper tests prove canonical inputs, determinism, and purpose separation while synchronous harnesses prove atomic propagation without implementing STUB producers. | PASS |
| 6. Verificación obligatoria | Constraints, migrations, concurrency, harness rollback, seeding, ownership, backlog traceability, and structural accessibility have explicit automated acceptance tests. | PASS |
| 7. Main siempre desplegable | CI remains blocking and gains explicit SQLite and PostgreSQL contract suites. | PASS |
| 8. Monolito modular | Work remains inside `accounts`, `catalog`, `learning`, `gamification`, `analytics`, and `ui`; no infrastructure is added. | PASS |
| 9. Entrega simple e incremental | Only shared foundations and the explicitly implemented reads/constants/season resolver are delivered. | PASS |
| 10. Contenido trazable y versionado | ContentVersion stores author, source, version, review date, publication date, and immutable snapshot fields. | PASS |
| 11. Frontend server-rendered y accesible | Stable blocks and semantic navigation preserve visible keyboard focus, verified by fast rendered-HTML and style/class assertions without browser automation or manual review. | PASS |
| 12. Autorización en profundidad | Future mutating stubs document service-level authorization; this feature implements no authorization-sensitive mutation. | PASS |
| 13. Privacidad por minimización | Idempotency inputs are HMAC-digested; demo `.invalid` emails remain only in Account rows; output, rankings, events, and metrics omit private identity. | PASS |
| 14. Comunicación entre módulos | `learning` consumes only `attempt_registered`; `gamification` consumes it plus `session_completed`; cross-app reads remain behind published query contracts. | PASS |
| 15. Tiempo determinista | Weekly boundaries derive from `America/Bogota` and include Monday/Sunday boundary tests. | PASS |
| 16. Propiedad de archivos y migraciones | The closed manifest owns all touched paths and baseline migrations; automated drift checks cover all six baseline assignments and five backlog traces. | PASS |

SQLite execution is supplementary only. Migration correctness, exclusion constraints, idempotency concurrency, and audit/privacy acceptance are never inferred from SQLite and must pass against PostgreSQL.

### Post-Design Gate

Phase 1 artifacts preserve every pre-research gate. `data-model.md` assigns each entity and write responsibility to one app and distinguishes generic database, implemented-service, and future receiver/STUB invariants. `contracts/` freezes signatures, two event envelopes, integration surfaces, authority lifecycle, and ownership. `quickstart.md` requires both backends, uses harness evidence for STUB producers, tests digest behavior directly, verifies accessibility structurally, automates ownership/traceability acceptance, and identifies PostgreSQL-only evidence. No constitutional exception or complexity waiver is required.

## Architecture

### Persistence ownership

- `catalog` owns `ContentItem`, `ContentVersion`, `Choice`, and `LabExercise` in `catalog/migrations/0002_domain_content.py`.
- `learning` owns `Enrollment`, `Attempt`, and `Progress` in `learning/migrations/0001_initial.py`.
- `gamification` owns `ScoreEvent`, `Streak`, `WeeklySeason`, and `SeasonParticipation` in `gamification/migrations/0001_initial.py` and remains the sole writer of participation counters.
- `accounts` is not migrated: `Account.display_name` already satisfies the public-name contract.
- `analytics` owns result contracts and query stubs only; it receives no persistent model in this feature.

Foreign keys across apps use lazy model labels in model declarations. Runtime cross-app reads use published query services. Event consumers receive persisted facts through `attempt_registered` and `session_completed` rather than importing another app's services; `learning` never writes `SeasonParticipation` directly.

### Integrity strategy

- Portable `UniqueConstraint` and `CheckConstraint` objects enforce positive counters, bounded positions, unique relationships, one first scoreable attempt, and global idempotency digests on SQLite and PostgreSQL.
- `ScoreEvent` persistence accepts nonnegative amounts, an optional attempt, and requires an attempt only for cause `attempt`; it deliberately has no cause-specific constraint forcing `session_completed` to amount zero and no attempt. The future session receiver owns that semantic combination.
- Raw idempotency keys are accepted only at future service boundaries. `accounts.security.security_digest` hashes the complete attempt key with purpose `learning.attempt.idempotency`; attempt score events hash canonical `str(attempt.id)` with purpose `gamification.score-event.idempotency`. Only 64-character digests persist or cross event boundaries. Feature 004 inspects these contracts/docstrings and directly tests helper determinism and purpose separation; runtime producer use, replay, and retry remain future evidence.
- Published content snapshots, choices, and labs use the existing `ImmutableModel` behavior. Consecutive content positions and set-level publication rules are future service invariants checked under parent locks; this feature verifies their documented contract and creates only valid fixtures/demo data without implementing those STUB mutations.
- `WeeklySeason` uses portable ordered-date checks plus canonical Monday-Sunday construction in `current_season()`. Its migration conditionally installs a PostgreSQL exclusion constraint over an inclusive `daterange(starts_on, ends_on, '[]')`; SQLite skips only that vendor-specific operation. PostgreSQL is the acceptance authority for non-overlap and concurrent creation.

### Service and event boundaries

- Public mutable operations stay explicit STUBs that raise `NotImplementedError` before touching persistence.
- Implemented query functions use app-owned models, deterministic ordering, and `select_related`/`prefetch_related` where the return contract crosses relationships.
- Future producers call `attempt_registered.send()` and `session_completed.send()` synchronously inside `transaction.atomic`; receiver exceptions propagate and roll back producer and prior receiver writes.
- Feature 004 tests both envelopes, receiver order, duplicate registration, exception propagation, and rollback through explicit transaction harnesses. It does not claim producer creation, replay, or retry while producer functions remain STUBs.
- `learning.receivers` registers only its `attempt_registered` progress hook. `gamification.receivers` registers scoring, streak, and participation hooks for `attempt_registered` plus participation for `session_completed`; stable `dispatch_uid` values from each app's `AppConfig.ready()` prevent duplicate registration. Future gamification receivers are the sole writers of `SeasonParticipation` and enforce zero-amount, no-attempt `ScoreEvent` receipts for completed sessions.

### Composition boundaries

- Root URL composition includes `catalog`, `learning`, `gamification`, and `analytics` once. Learning owns four route modules under a URL package so parallel features do not share route files.
- `ui.navigation` discovers optional `NAV_ITEMS` from installed apps. Known entries are declared in each app now and unresolved URL names are omitted until their feature route exists, so future features do not edit the navigation template.
- `ui/templates/base.html` keeps the legacy `content` block nested inside the new `main` block and adds `sidebar`, `fragments`, and `scripts`, preserving existing templates while freezing future extension points. Fast tests inspect rendered semantic navigation and applicable focus rules/classes; this structural acceptance uses neither browser automation nor manual review.

## Project Structure

### Documentation (this feature)

```text
specs/004-domain-contracts/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── checklists/requirements.md
├── contracts/
│   ├── services.md
│   ├── domain-events.md
│   ├── integration-surfaces.md
│   └── ownership.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
catalog/
├── models.py
├── nav.py
├── migrations/0002_domain_content.py
└── services/content.py
learning/
├── apps.py
├── models.py
├── nav.py
├── receivers.py
├── signals.py
├── migrations/0001_initial.py
├── services/{__init__,attempts,enrollment,progress,session}.py
├── urls/{__init__,attempts,enrollment,progress,session}.py
└── views/__init__.py
gamification/
├── apps.py
├── models.py
├── nav.py
├── receivers.py
├── urls.py
├── migrations/0001_initial.py
└── services/{__init__,scoring,seasons,streaks}.py
analytics/
├── nav.py
├── urls.py
└── services/{__init__,metrics}.py
ui/
├── context_processors.py
├── nav.py
├── navigation.py
├── management/commands/seed_demo.py
└── templates/base.html
kronolearn/
├── settings/base.py
└── urls.py
templates/{catalog/content,learning/{attempts,enrollment,progress,session},gamification,analytics}/
tests/{analytics,catalog,factories,gamification,integration,learning,ui}/
docs/contracts/domain-contracts.md
.github/workflows/ci.yml
CHANGELOG.md
```

**Structure Decision**: Extend the existing flat Django apps rather than introduce a shared-domain app. Each model and service remains with the module that owns its write rules; only root composition, navigation discovery, and demo orchestration cross app boundaries. Empty reserved template directories use `.gitkeep`, while equivalent test and Python package directories use empty `__init__.py` files.

## File Ownership Manifest

This feature may create or modify only the paths named in this section. No change to `accounts/models.py`, existing catalog behavior, dependency lockfiles, deployment configuration, or feature specs 001-003 is allowed.

**Existing files allowed to change**:

- `.github/workflows/ci.yml`
- `CHANGELOG.md`
- `catalog/models.py`
- `catalog/services/content.py`
- `gamification/apps.py`
- `kronolearn/settings/base.py`
- `kronolearn/urls.py`
- `learning/apps.py`
- `ui/templates/base.html`
- `specs/004-domain-contracts/spec.md`
- `specs/004-domain-contracts/checklists/requirements.md`
- `specs/004-domain-contracts/plan.md`

**New files allowed**:

- `accounts/nav.py`, `catalog/nav.py`, `learning/nav.py`, `gamification/nav.py`, `analytics/nav.py`, `ui/nav.py`
- `catalog/migrations/0002_domain_content.py`
- `learning/models.py`, `learning/signals.py`, `learning/receivers.py`, `learning/migrations/0001_initial.py`
- `learning/services/__init__.py`, `learning/services/attempts.py`, `learning/services/enrollment.py`, `learning/services/progress.py`, `learning/services/session.py`
- `learning/urls/__init__.py`, `learning/urls/attempts.py`, `learning/urls/enrollment.py`, `learning/urls/progress.py`, `learning/urls/session.py`, `learning/views/__init__.py`
- `gamification/models.py`, `gamification/receivers.py`, `gamification/urls.py`, `gamification/migrations/0001_initial.py`
- `gamification/services/__init__.py`, `gamification/services/scoring.py`, `gamification/services/seasons.py`, `gamification/services/streaks.py`
- `analytics/urls.py`, `analytics/services/__init__.py`, `analytics/services/metrics.py`
- `ui/context_processors.py`, `ui/navigation.py`, `ui/management/__init__.py`, `ui/management/commands/__init__.py`, `ui/management/commands/seed_demo.py`
- `templates/catalog/content/.gitkeep`, `templates/learning/attempts/.gitkeep`, `templates/learning/enrollment/.gitkeep`, `templates/learning/progress/.gitkeep`, `templates/learning/session/.gitkeep`, `templates/gamification/.gitkeep`, `templates/analytics/.gitkeep`
- `tests/factories/__init__.py`, `tests/factories/accounts.py`, `tests/factories/catalog.py`, `tests/factories/gamification.py`, `tests/factories/learning.py`
- `tests/catalog/content/__init__.py`, `tests/learning/attempts/__init__.py`, `tests/learning/enrollment/__init__.py`, `tests/learning/progress/__init__.py`, `tests/learning/session/__init__.py`
- `tests/catalog/test_domain_contracts.py`
- `tests/learning/__init__.py`, `tests/learning/test_attempt_contracts.py`, `tests/learning/test_enrollment_contracts.py`, `tests/learning/test_models.py`, `tests/learning/test_progress_contracts.py`, `tests/learning/test_session_contracts.py`, `tests/learning/test_signals.py`
- `tests/gamification/__init__.py`, `tests/gamification/test_models.py`, `tests/gamification/test_scoring_contracts.py`, `tests/gamification/test_seasons.py`, `tests/gamification/test_streak_contracts.py`
- `tests/analytics/__init__.py`, `tests/analytics/test_metrics_contracts.py`
- `tests/integration/__init__.py`, `tests/integration/test_domain_migrations.py`, `tests/integration/test_domain_privacy.py`, `tests/integration/test_root_contracts.py`, `tests/integration/test_seed_demo.py`
- `tests/ui/test_base_contract.py`, `tests/ui/test_navigation_contract.py`
- `docs/contracts/domain-contracts.md`
- `specs/004-domain-contracts/research.md`, `specs/004-domain-contracts/data-model.md`, `specs/004-domain-contracts/quickstart.md`
- `specs/004-domain-contracts/contracts/services.md`, `specs/004-domain-contracts/contracts/domain-events.md`, `specs/004-domain-contracts/contracts/integration-surfaces.md`, `specs/004-domain-contracts/contracts/ownership.md`
- `specs/004-domain-contracts/tasks.md`

After merge, the three migrations, domain model files, `learning/signals.py`, root URL composition, base template, navigation discovery and declarations, and URL aggregators are frozen shared surfaces. Changes require an explicit contract amendment and coordinated ownership.

### Parallel feature ownership after merge

| Feature | Writable implementation paths | Consumed contracts |
| --- | --- | --- |
| Autoría de contenido | `catalog/services/content.py`, `templates/catalog/content/**`, `tests/catalog/content/**` | Content models and catalog service signatures |
| Inscripción | `learning/services/enrollment.py`, `learning/urls/enrollment.py`, `learning/views/enrollment/**`, `templates/learning/enrollment/**`, `tests/learning/enrollment/**` | Enrollment model and enrollment services |
| Sesión diaria | `learning/services/session.py`, `learning/urls/session.py`, `learning/views/session/**`, `templates/learning/session/**`, `tests/learning/session/**` | Content queries, Enrollment, Progress, session services |
| Intento y retroalimentación | `learning/services/attempts.py`, `learning/urls/attempts.py`, `learning/views/attempts/**`, `templates/learning/attempts/**`, `tests/learning/attempts/**` | Attempt, AttemptResult, attempt_registered |
| Ruta y progreso | `learning/services/progress.py`, `learning/receivers.py`, `learning/urls/progress.py`, `learning/views/progress/**`, `templates/learning/progress/**`, `tests/learning/progress/**` | Progress, TrackProgress, attempt_registered |
| Puntos, racha y participación | `gamification/services/scoring.py`, `gamification/services/streaks.py`, `gamification/receivers.py`, `templates/gamification/**`, `tests/gamification/scoring/**`, `tests/gamification/streaks/**` | ScoreEvent, Streak, SeasonParticipation, constants, attempt_registered, session_completed |
| Liga semanal | `gamification/services/seasons.py`, `gamification/urls.py`, `templates/gamification/leaderboard/**`, `tests/gamification/seasons/**` | WeeklySeason, SeasonParticipation, LeaderboardEntry |
| Métricas administrativas | `analytics/services/metrics.py`, `analytics/urls.py`, `templates/analytics/**`, `tests/analytics/metrics/**` | ContentMetrics and EngagementMetrics |
| Insignias | New app-owned paths approved by amendment; no baseline model edits | Attempt, Progress, ScoreEvent, Streak query contracts |
| Repaso | New learning paths approved by amendment; no baseline model edits | Attempt and Progress query contracts |
| Meta semanal | New gamification paths approved by amendment; no baseline model edits | SeasonParticipation query contract |

## Implementation Strategy

1. Establish failing model and migration contract tests, then add the three app-owned schema migrations and immutable model definitions.
2. Establish import/signature tests, then add immutable result types, constants, implemented reads, and side-effect-free STUBs.
3. Establish transactional harness and exact per-app registration tests, then add `attempt_registered`, `session_completed`, receiver modules, and `ready()` imports with `dispatch_uid`; leave producer behavior to later features.
4. Establish root URL, template-block, navigation-discovery, semantic-markup, and focus-rule tests, then freeze composition surfaces and reserved directories without browser automation.
5. Establish factory and command tests, then add deterministic factories and transactional `seed_demo` with private `.invalid` account keys, an explicit `--confirm-production` flag, and unusable passwords outside debug mode.
6. Generate the final human source-of-truth contract document from the approved design and run automated contract drift assertions against public symbols, six baseline ownership assignments, and five backlog traces.
7. Run the fast SQLite suite, then the full PostgreSQL migration/concurrency/audit suite, Django checks, migration drift checks, Ruff, and documentation validation.

Every implementation unit follows red-green-refactor and ends with its narrowest test before broader validation. Commit boundaries should follow the seven units above; do not combine unrelated app ownership in a commit except the intentionally shared composition and documentation units.

## Complexity Tracking

No constitutional violations require justification. The PostgreSQL-only exclusion constraint is a required integrity guarantee, not an additional service or infrastructure dependency; SQLite remains a fast compatibility check and is not treated as acceptance evidence for non-overlap or concurrency.
