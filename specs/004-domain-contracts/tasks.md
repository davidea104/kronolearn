---

description: "Implementation tasks for shared domain contracts and skeleton"
---

# Tasks: Contratos y esqueleto de dominio

**Input**: Design documents from `specs/004-domain-contracts/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by FR-046 and FR-047. Every implementation slice follows red-green-refactor and runs its narrowest test before broader validation.

**Organization**: Tasks are grouped by user story. Shared schema is foundational because every story consumes it; story phases remain independently testable at their documented boundary.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and has no dependency on another incomplete task in the same batch.
- **[Story]**: Maps the task to a user story from `spec.md`.
- Every task includes exact repository-relative file paths and requirement keys for traceability.

## Phase 1: Setup (Shared Structure)

**Purpose**: Create only the package and reserved-directory skeleton needed by later tasks; add no functional endpoint or workflow.

- [X] T001 Create empty Python package markers in `learning/services/__init__.py`, `learning/views/__init__.py`, `learning/urls/__init__.py`, `gamification/services/__init__.py`, `analytics/services/__init__.py`, `ui/management/__init__.py`, `ui/management/commands/__init__.py`, `tests/catalog/content/__init__.py`, `tests/learning/__init__.py`, `tests/learning/enrollment/__init__.py`, `tests/learning/session/__init__.py`, `tests/learning/attempts/__init__.py`, `tests/learning/progress/__init__.py`, `tests/gamification/__init__.py`, `tests/analytics/__init__.py`, `tests/integration/__init__.py`, and `tests/factories/__init__.py`, keeping service and view initializers free of re-exports (FR-032, FR-033)
- [X] T002 [P] Reserve template ownership with `.gitkeep` files at `templates/catalog/content/.gitkeep`, `templates/learning/enrollment/.gitkeep`, `templates/learning/session/.gitkeep`, `templates/learning/attempts/.gitkeep`, `templates/learning/progress/.gitkeep`, `templates/gamification/.gitkeep`, and `templates/analytics/.gitkeep` (FR-032)

---

## Phase 2: Foundational (Blocking Domain Schema)

**Purpose**: Establish the complete shared persistence model and migration graph before any public service or story integration is implemented.

**Critical**: All user-story work depends on completion of this phase.

### Foundational tests first

- [X] T003 [P] Add failing catalog entity tests for positive unique per-parent positions and snapshot immutability, while leaving consecutive positions and publishable choice-set validation to future locked services, in `tests/catalog/test_domain_contracts.py` (FR-006-FR-009, FR-043, FR-044)
- [X] T004 [P] Add failing enrollment, attempt, progress, cross-relation, first-scoreable, and idempotency constraint tests in `tests/learning/test_models.py` (FR-010-FR-012, FR-043)
- [X] T005 [P] Add failing score event tests for generic nonnegative-amount, optional-attempt, attempt-cause reference, and digest constraints, including acceptance of a zero-amount no-attempt `session_completed` row without a cause-specific constraint, plus streak, ordered weekly-season dates, participation uniqueness, and counter constraint tests in `tests/gamification/test_models.py`, reserving receiver semantics and canonical Monday-Sunday creation for their future service tests (FR-013-FR-016, FR-043)
- [X] T006 [P] Add failing clean-install migration graph and model inventory tests for all 11 entities in `tests/integration/test_domain_migrations.py` (FR-003, FR-046, SC-003)

### Foundational implementation

- [X] T007 Implement `ContentItem`, immutable `ContentVersion`, immutable `Choice`, and immutable `LabExercise` with enums, relationships, database-level positive/bounded position checks, per-parent uniqueness, and derived `is_current` in `catalog/models.py`, without implementing future consecutive-position or publishable-set services (FR-006-FR-009)
- [X] T008 Create the catalog schema, indexes, constraints, permissions, and immutable snapshot migration in `catalog/migrations/0002_domain_content.py` (FR-003, FR-006-FR-009, FR-043, FR-044)
- [X] T009 Implement `Enrollment`, immutable `Attempt`, and `Progress` with protected relationships, global digest uniqueness, one first-scoreable attempt, and counter checks in `learning/models.py` (FR-010-FR-012, FR-043)
- [X] T010 Create the learning schema, indexes, constraints, and dependency on `catalog.0002_domain_content` in `learning/migrations/0001_initial.py` (FR-003, FR-010-FR-012, FR-043)
- [X] T011 Implement `ScoreEvent` with generic nonnegative-amount, optional-attempt, attempt-cause reference, and digest constraints that accept a zero-amount no-attempt `session_completed` row without enforcing that future receiver invariant by cause, plus `Streak`, `WeeklySeason`, and `SeasonParticipation` with protected relationships, uniqueness, and counter/date checks in `gamification/models.py` (FR-013-FR-016, FR-043)
- [X] T012 Create the gamification schema plus conditional PostgreSQL inclusive-date-range exclusion constraint in `gamification/migrations/0001_initial.py` (FR-003, FR-013-FR-016, FR-043)
- [ ] T013 Run the narrow model and migration tests from T003-T006 on SQLite and PostgreSQL and record any backend-specific assertions in `tests/integration/test_domain_migrations.py` (FR-046, FR-047, SC-003)

**Checkpoint**: A clean database exposes all 11 entities and portable constraints; PostgreSQL additionally enforces non-overlapping seasons.

---

## Phase 3: User Story 1 - Desarrollar features en paralelo sobre contratos estables (Priority: P1) - MVP

**Goal**: Make every shared service, type, event, route, template block, navigation declaration, and ownership boundary importable without implementing later business workflows.

**Independent Test**: From six clean branches, import each assigned contract and resolve its reserved integration path without editing a model, migration, root URL, base template, navigation registry, or another feature's files.

### US1 tests first

- [X] T014 [P] [US1] Add failing tests for the four catalog service signatures, deterministic current-version queries, and side-effect-free STUBs in `tests/catalog/test_domain_contracts.py` (FR-004, FR-005, FR-023)
- [X] T015 [P] [US1] Add failing enrollment service signature, ordering, eager-loading, and STUB tests in `tests/learning/test_enrollment_contracts.py` (FR-004, FR-005, FR-023)
- [X] T016 [P] [US1] Add failing session service signature and side-effect-free STUB tests in `tests/learning/test_session_contracts.py` (FR-004, FR-005)
- [X] T017 [P] [US1] Add failing `AttemptResult`, attempt query ordering, and attempt STUB tests in `tests/learning/test_attempt_contracts.py` (FR-004, FR-005, FR-018, FR-023)
- [X] T018 [P] [US1] Add failing `TrackProgress` shape, empty-state semantics, and progress STUB tests in `tests/learning/test_progress_contracts.py` (FR-004, FR-005, FR-019)
- [X] T019 [P] [US1] Add failing `RATING_POINTS`, `ScoreEvent` return contract, and scoring STUB tests in `tests/gamification/test_scoring_contracts.py` (FR-004, FR-005, FR-013, FR-021)
- [X] T020 [P] [US1] Add failing streak constants, return contract, project-date semantics, and STUB tests in `tests/gamification/test_streak_contracts.py` (FR-004, FR-005, FR-014, FR-022)
- [X] T021 [P] [US1] Add failing canonical Monday-Sunday resolver, aware-datetime, stable leaderboard projection, and STUB tests in `tests/gamification/test_seasons.py` (FR-004, FR-005, FR-015, FR-020, FR-023)
- [X] T022 [P] [US1] Add failing immutable metric projection, suppression, privacy, and metrics STUB tests in `tests/analytics/test_metrics_contracts.py` (FR-004, FR-005, FR-017, FR-020)
- [X] T023 [P] [US1] Add failing tests for exact `attempt_registered(attempt, result)` and `session_completed(enrollment, completed_at, idempotency_key)` envelopes, pre-derived session digest delivery, temporary receiver order, synchronous error propagation, duplicate registration, and the exact subscription matrix where `learning` consumes only `attempt_registered` and `gamification` consumes both events in `tests/learning/test_signals.py` (FR-024-FR-027)
- [X] T024 [P] [US1] Add failing namespace, route-module, empty-initializer, and no-new-workflow tests in `tests/integration/test_root_contracts.py` (FR-001, FR-002, FR-028, FR-029, FR-033)
- [X] T025 [P] [US1] Add failing fast rendered-HTML tests for overrides of `title`, `main`, nested `content`, `sidebar`, `fragments`, and `scripts`, semantic `nav`, and applicable visible-focus rules or classes in `tests/ui/test_base_contract.py`, without browser automation or manual checks (FR-030, FR-046)
- [X] T026 [P] [US1] Add failing distributed navigation discovery, authorization filtering, duplicate-key check, deterministic ordering, and unresolved-route tests in `tests/ui/test_navigation_contract.py` (FR-017, FR-031)

### US1 service and type implementation

- [X] T027 [P] [US1] Add exact public signatures, complete STUB docstrings, `get_published_version`, and `list_published_versions` to `catalog/services/content.py` (FR-004, FR-005, FR-023, FR-042)
- [X] T028 [P] [US1] Implement exact enrollment signatures, complete STUB docstring, deterministic implemented reads, and future authorization/idempotency semantics in `learning/services/enrollment.py` (FR-004, FR-005, FR-023, FR-042)
- [X] T029 [P] [US1] Implement exact session STUB signatures and complete contract docstrings without direct catalog model queries in `learning/services/session.py` (FR-004, FR-005, FR-042)
- [X] T030 [P] [US1] Add frozen `AttemptResult`, exact attempt signatures, a side-effect-free `register_attempt` STUB documenting `security_digest(idempotency_key, purpose="learning.attempt.idempotency")`, and deterministic `list_attempts` query in `learning/services/attempts.py` (FR-004, FR-005, FR-011, FR-018, FR-023, FR-042)
- [X] T031 [P] [US1] Add frozen `TrackProgress`, exact progress STUBs, complete docstrings, percentage bounds, module ordering, and `accuracy=None` empty semantics in `learning/services/progress.py` (FR-004, FR-005, FR-019, FR-042)
- [X] T032 [P] [US1] Add immutable `RATING_POINTS` and a side-effect-free scoring STUB documenting one-event semantics plus `security_digest(str(attempt.id), purpose="gamification.score-event.idempotency")` in `gamification/services/scoring.py` (FR-004, FR-005, FR-013, FR-021, FR-042)
- [X] T033 [P] [US1] Add `STREAK_BONUS_STEP`, `STREAK_BONUS_CAP`, exact streak STUBs, project-date semantics, and complete docstrings in `gamification/services/streaks.py` (FR-004, FR-005, FR-014, FR-022, FR-042)
- [X] T034 [P] [US1] Add frozen `LeaderboardEntry`, implement concurrency-safe `current_season` as the public path that derives the project-timezone Monday-Sunday interval, and add the exact privacy-preserving leaderboard STUB in `gamification/services/seasons.py` (FR-004, FR-005, FR-015, FR-017, FR-020, FR-023, FR-042)
- [X] T035 [P] [US1] Add frozen `ContentMetrics` and `EngagementMetrics`, immutable numeric maps, exact suppressed STUBs, and complete docstrings in `analytics/services/metrics.py` (FR-004, FR-005, FR-017, FR-020, FR-042)

### US1 event and composition implementation

- [X] T036 [US1] Define public `attempt_registered` and `session_completed` signals with the documented named envelopes in `learning/signals.py`, without implementing either producer (FR-004, FR-024, FR-025)
- [X] T037 [P] [US1] Register only the wiring-only learning progress hook for `attempt_registered`, with a stable `dispatch_uid` from `LearningConfig.ready()`, in `learning/receivers.py` and `learning/apps.py`, without subscribing learning to `session_completed`, implementing domain behavior, or importing consumer services from the producer (FR-026, FR-027)
- [X] T038 [P] [US1] Register wiring-only gamification scoring, streak, and participation hooks for `attempt_registered` plus the participation hook for `session_completed`, each with a stable `dispatch_uid` from `GamificationConfig.ready()`, in `gamification/receivers.py` and `gamification/apps.py`, without implementing domain behavior and keeping `gamification` the sole future writer of `SeasonParticipation` (FR-016, FR-026, FR-027)
- [X] T039 [P] [US1] Create reserved learning route modules and the namespaced aggregator in `learning/urls/enrollment.py`, `learning/urls/session.py`, `learning/urls/attempts.py`, `learning/urls/progress.py`, and `learning/urls/__init__.py` without functional views (FR-001, FR-028, FR-029)
- [X] T040 [P] [US1] Create namespaced reserved aggregators without functional routes in `gamification/urls.py` and `analytics/urls.py` (FR-001, FR-028)
- [X] T041 [US1] Include catalog, learning, gamification, and analytics exactly once while preserving existing routes in `kronolearn/urls.py` (FR-002, FR-028, FR-034)
- [X] T042 [P] [US1] Implement frozen `NavItem`, optional app discovery, duplicate checks, authorization filtering, unresolved-route omission, and deterministic sorting in `ui/navigation.py` (FR-017, FR-031, FR-034)
- [X] T043 [P] [US1] Declare immutable navigation tuples in `accounts/nav.py`, `catalog/nav.py`, `learning/nav.py`, `gamification/nav.py`, `analytics/nav.py`, and `ui/nav.py` (FR-031, FR-034)
- [X] T044 [US1] Expose `primary_navigation` through `ui/context_processors.py` and register the processor in `kronolearn/settings/base.py` (FR-031)
- [X] T045 [US1] Add stable `main`, `sidebar`, `fragments`, and `scripts` blocks while retaining `title`, nesting legacy `content`, preserving semantic navigation, and exposing the existing visible-focus rule or class in `ui/templates/base.html` (FR-002, FR-030, FR-034)
- [X] T046 [US1] Run all US1 contract tests and verify six ownership consumers need no shared edits, recording the executable import matrix in `tests/integration/test_root_contracts.py` (FR-005, FR-034, SC-001, SC-002)

**Checkpoint**: All six baseline teams can import and locate their stable contracts; no learner or administrator workflow has been added.

---

## Phase 4: User Story 2 - Validar una línea base íntegra y desacoplada (Priority: P1)

**Goal**: Prove persistence invariants, concurrency, immutability, transactional event semantics, and privacy on both supported storage environments.

**Independent Test**: Apply all migrations to an empty PostgreSQL database, exercise valid and invalid rows plus concurrent writers, and use explicit transactional harnesses to deliver both event envelopes without invoking either STUB producer or importing a consumer from a producer.

### US2 tests and verification

- [X] T047 [P] [US2] After T034, extend PostgreSQL tests with the persistence-level non-overlap exclusion and concurrent `current_season` identity checks in `tests/integration/test_domain_migrations.py`, leaving canonical Monday-Sunday derivation in `tests/gamification/test_seasons.py` (FR-015, FR-043, FR-046, SC-005)
- [X] T048 [P] [US2] Add PostgreSQL concurrent uniqueness tests for enrollment, attempt digests, first-scoreable attempts, score event digests, and one score event per attempt in `tests/learning/test_attempt_contracts.py` and `tests/gamification/test_scoring_contracts.py` (FR-010, FR-011, FR-013, FR-043, FR-046, SC-005)
- [X] T049 [P] [US2] Add explicit `transaction.atomic()` harness tests for both event envelopes, receiver order, synchronous exception propagation, rollback of harness and prior receiver writes, and duplicate-registration protection in `tests/learning/test_signals.py`, excluding producer creation, committed replay, and same-key retry claims (FR-024-FR-027, FR-046)
- [X] T050 [P] [US2] Add automated contract/docstring inspection for the exact digest inputs and purposes, direct `security_digest` determinism and purpose-separation tests, and checks that raw idempotency inputs never persist or cross event boundaries and demo `.invalid` emails occur only in authoritative `Account` rows and never in captured output, events, audit, rankings, or metrics in `tests/integration/test_domain_privacy.py`, without invoking STUB producers or claiming runtime integration (FR-011, FR-013, FR-017, FR-020, FR-045, FR-046, SC-008)
- [ ] T051 [US2] Run the full contract matrix on SQLite and PostgreSQL and encode only PostgreSQL-valid concurrency, exclusion, migration, and audit assertions in `tests/integration/test_domain_migrations.py` (FR-046, FR-047, SC-003, SC-005, SC-007)

**Checkpoint**: The same portable matrix passes on both backends, with PostgreSQL-only evidence for migrations, exclusions, concurrency, rollback, and persistence privacy.

---

## Phase 5: User Story 3 - Preparar y repetir un entorno de demostración (Priority: P2)

**Goal**: Provide deterministic factories and one safe, transactional, idempotent command that creates the exact minimal demo graph.

**Independent Test**: Run `seed_demo` twice and confirm unchanged logical identities and counts for two tracks, two contents, two accounts, and the current season; reject an unconfirmed non-debug run before any write.

### US3 tests first

- [X] T052 [P] [US3] Add failing valid-default and override tests for every new entity plus required Account, Track, and Module relationships in `tests/catalog/test_domain_contracts.py`, `tests/learning/test_models.py`, and `tests/gamification/test_models.py` (FR-038)
- [X] T053 [P] [US3] Add failing clean-seed, repeat-seed identity/count, incomplete-demo repair, unrelated-data preservation, reserved `.invalid` account-key storage, production refusal, unusable-password, output privacy, and two-minute budget tests in `tests/integration/test_seed_demo.py` (FR-035-FR-037, FR-045, SC-004, SC-008)

### US3 implementation

- [X] T054 [P] [US3] Implement deterministic account, track, module, content, version, choice, and lab factories in `tests/factories/accounts.py` and `tests/factories/catalog.py` without adding a dependency (FR-038)
- [X] T055 [P] [US3] Implement deterministic enrollment, attempt, progress, score event, streak, season, and participation factories in `tests/factories/learning.py` and `tests/factories/gamification.py` (FR-038)
- [X] T056 [US3] Implement atomic natural-key `seed_demo` with deterministic non-personal `.invalid` emails stored only on demo `Account` rows, the exact named graph, repair-only behavior, `--confirm-production`, unusable non-debug passwords, and counts/public-title-only output in `ui/management/commands/seed_demo.py` (FR-035-FR-037, FR-045)
- [ ] T057 [US3] Run the seed twice on SQLite and PostgreSQL and retain deterministic count, identity, safety, and duration assertions in `tests/integration/test_seed_demo.py` (FR-035-FR-037, FR-046, FR-047, SC-004)

**Checkpoint**: A developer can create the complete shared demo graph in under two minutes and repeat the operation without duplication or secret disclosure.

---

## Phase 6: User Story 4 - Planificar backlog sin alterar la línea base (Priority: P3)

**Goal**: Publish one authoritative contract document from which baseline and backlog owners can identify data sources, writable paths, and frozen surfaces without verbal clarification.

**Independent Test**: Automated ownership and traceability tests validate all six baseline assignments and five backlog reservations against the authoritative document; no two baseline features share an editable path and no backlog trace requires a schema change.

### US4 tests first

- [X] T058 [US4] Add failing documentation drift tests for all 11 models, 20 signatures, five projection types, constants, both signal envelopes, template blocks, namespaces, and STUB/IMPLEMENT states in `tests/integration/test_root_contracts.py` (FR-005, FR-039, SC-003)
- [X] T059 [US4] Add failing automated ownership and traceability tests for all six disjoint baseline path sets, all five backlog reservations, the frozen surfaces listed by the ownership contract, one migration owner per app, and gamification-only participation writes in `tests/integration/test_root_contracts.py`, treating `specs/004-domain-contracts/tasks.md` as part of the implementation manifest rather than a frozen post-merge surface (FR-016, FR-034, FR-040, FR-041, SC-002, SC-006, SC-009)

### US4 documentation and review

- [X] T060 [P] [US4] Create the single human source of truth at implementation completion with entity diagram, exact services and result types, both event envelopes and harness boundary, integration surfaces, digest derivations, STUB docstring policy, and cross-links in `docs/contracts/domain-contracts.md` (FR-005, FR-039, FR-042)
- [X] T061 [US4] Add the non-overlapping six-feature ownership matrix, frozen-path policy, migration ownership, and five backlog read traces to `docs/contracts/domain-contracts.md` (FR-040, FR-041, SC-006, SC-009)
- [X] T062 [P] [US4] Add the automated six-baseline-assignment and five-backlog-trace acceptance procedure to `specs/004-domain-contracts/quickstart.md`, with no timed human review dependency (SC-006, SC-009)
- [X] T063 [US4] Execute the automated documentation drift, ownership, and backlog traceability tests and confirm complete six-baseline and five-backlog coverage in `docs/contracts/domain-contracts.md` (FR-039-FR-041, SC-006, SC-009)

**Checkpoint**: Every baseline and backlog owner can plan from the authoritative document without modifying a frozen contract.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Integrate the acceptance gates without expanding product scope.

- [X] T064 [P] Add SQLite and PostgreSQL contract jobs, migration drift checks, and authoritative concurrency/audit execution to `.github/workflows/ci.yml` (FR-047, SC-007)
- [X] T065 [P] Document the shared contracts, migration ownership, demo command, and absence of functional workflows in `CHANGELOG.md` (FR-001, FR-002)
- [ ] T066 Run Ruff, Django checks, migration drift, the focused SQLite suite, the full PostgreSQL suite, seed idempotency, privacy scans, and existing regression tests exactly as documented in `specs/004-domain-contracts/quickstart.md` (FR-002, FR-045-FR-047, SC-003-SC-005, SC-007, SC-008)
- [X] T067 Compare public code and the final authority `docs/contracts/domain-contracts.md` against planning inputs `specs/004-domain-contracts/spec.md`, `specs/004-domain-contracts/contracts/services.md`, `specs/004-domain-contracts/contracts/domain-events.md`, `specs/004-domain-contracts/contracts/integration-surfaces.md`, and `specs/004-domain-contracts/contracts/ownership.md`, resolving every detected drift before completion (FR-005, FR-039-FR-042)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; it is the MVP and establishes public contracts consumed by later phases.
- **Phase 4 (US2)**: Depends on Phase 2 and the event/query surfaces from US1.
- **Phase 5 (US3)**: Depends on Phase 2 and `current_season` from US1; otherwise independent of US2.
- **Phase 6 (US4)**: Depends on US1 contract surfaces; it can proceed in parallel with US2 and US3 after US1.
- **Phase 7 (Polish)**: Depends on all user stories.

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 (MVP) -> US2
                                  |-> US3
                                  |-> US4
US2 + US3 + US4 -> Polish
```

### Within Each Story

1. Write the listed failing contract tests.
2. Implement only the smallest contract slice needed to pass them.
3. Run the narrow test module before editing the next slice.
4. Finish with the story's independent test and checkpoint.

## Parallel Opportunities

### Foundational

After T001-T002, tasks T003-T006 can run in parallel. Catalog T007-T008 must finish before learning T009-T010; gamification T011-T012 follows learning because its migration references `Attempt`.

### User Story 1

```text
T014 -> T027  catalog contracts
T015 -> T028  enrollment contracts
T016 -> T029  session contracts
T017 -> T030  attempt contracts
T018 -> T031  progress contracts
T019 -> T032  scoring contracts
T020 -> T033  streak contracts
T021 -> T034  season contracts
T022 -> T035  metrics contracts
T023 -> T036 -> T037/T038  event wiring
T024 -> T039/T040 -> T041  URL composition
T025 -> T045  base template
T026 -> T042 -> T043 -> T044  navigation
```

The first ten test tasks use distinct test files except the already-sequenced catalog file. Service implementations T027-T035 use distinct owner modules and may proceed in parallel after their matching tests fail for the expected reason.

### User Story 2

```text
T047  season exclusion and concurrency
T048  uniqueness concurrency
T049  transactional event harnesses
T050  privacy boundaries
T047 + T048 + T049 + T050 -> T051
```

T047-T050 target separate integrity concerns and can run in parallel after US1. T051 is the convergence gate.

### User Story 3

```text
T052 + T053  failing factory and seed tests
T052 -> T054/T055
T053 + T054 + T055 -> T056 -> T057
```

T052 and T053 can be authored in parallel. Factory tasks T054 and T055 can run in parallel after T052; T056 follows the failing seed test and both factory tasks.

### User Story 4

```text
T058 -> T059
T059 -> T060/T062
T060 -> T061
T061 + T062 -> T063
```

T058 and T059 describe separate assertions but share `tests/integration/test_root_contracts.py`, so execute them sequentially or coordinate one owner. T060 and T062 use separate artifacts and can run in parallel; T061 follows T060 because both edit the authoritative document.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete US1 and run T046.
3. Stop and verify that all six baseline teams can import contracts and work only in assigned paths.

### Incremental Delivery

1. Deliver US1 as the importable shared-contract baseline.
2. Add US2 as authoritative integrity and concurrency evidence.
3. Add US3 as deterministic developer/demo setup.
4. Add US4 as backlog traceability and ownership governance.
5. Run the final dual-backend and drift gates.

### Scope Guard

- Do not implement any service marked STUB beyond its exact signature, docstring, immutable constants/types, and immediate side-effect-free `NotImplementedError`.
- Do not add learner or administrator screens, domain actions, external services, queues, workers, Redis, cron, or new dependencies.
- Stop and request a contract amendment before adding a model, migration, shared route, template block, public field, or public signature not listed in the design artifacts.
