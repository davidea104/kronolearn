---

description: "Implementation tasks for the KronoLearn public landing page"
---

# Tasks: Portada pública de KronoLearn

**Input**: Design documents from `specs/006-public-landing/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/public-landing.md](contracts/public-landing.md), [quickstart.md](quickstart.md)

**Tests**: Required by the specification and constitution. Write each story test first, confirm the expected failure, implement the smallest change, then rerun the focused command before continuing.

**Organization**: Tasks are grouped by user story and preserve the closed implementation file list from `plan.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and has no dependency on incomplete work.
- **[Story]**: Maps the task to a user story from `spec.md`.
- Every task names the exact file it changes or validates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm that the existing project already supplies the app, template engine, authentication routes, shared components, test runner and lint tools.

No setup task is required. This feature adds no dependency, directory outside the approved design, setting or migration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Identify shared infrastructure required before user-story work.

No foundational implementation is required. `ui`, `base.html`, `button.html`, account routes, `ui:learner-home` and `active_account_required` already exist and remain unchanged.

**Checkpoint**: Existing foundation is ready; begin User Story 1.

---

## Phase 3: User Story 1 - Conocer KronoLearn y elegir cómo entrar (Priority: P1) MVP

**Goal**: A visitor can open `/`, understand KronoLearn and choose registration or login.

**Independent Test**: Without a session, resolve `/`, request it and confirm `ui:index`, status `200`, `ui/index.html`, static purpose copy, one level-one heading, and links to `accounts:register` and `accounts:login` rendered through the shared button component.

### Tests for User Story 1

- [ ] T001 [US1] Create failing `test_root_resolves_to_ui_index`, `test_visitor_sees_public_landing_and_account_actions`, and `test_visitor_landing_is_static_and_excludes_out_of_scope_sections` cases in `tests/ui/test_public_landing.py`, covering `ui:index`, status `200`, `ui/index.html`, zero database queries for the anonymous request, purpose copy, one `<h1>`, absence of blog/prices/testimonials/contact/language content, and registration/login destinations scoped to the landing `<main>` so links in `ui/templates/base.html` cannot satisfy the assertions; confirm “Continuar aprendiendo” is absent, verify the shared button output, then run `manage.py test tests.ui.test_public_landing --settings=kronolearn.settings.test -v 2` and confirm failure before implementation

### Implementation for User Story 1

- [ ] T002 [US1] Add only `index(request)` rendering `ui/index.html` in `ui/views.py` and `path("", views.index, name="index")` before the existing routes in `ui/urls.py`; rerun the route test in `tests/ui/test_public_landing.py` and confirm it passes while the template test still fails
- [ ] T003 [US1] Create the static visitor experience in `templates/ui/index.html` by extending `base.html`, adding concise KronoLearn purpose copy and semantic structure, and including `ui/components/button.html` for `accounts:register` and `accounts:login` without models, forms, JavaScript, duplicated component markup or out-of-scope sections; rerun `tests.ui.test_public_landing` and confirm all US1 tests pass

**Checkpoint**: The visitor-facing landing page is independently functional and is the MVP.

---

## Phase 4: User Story 2 - Continuar al espacio de aprendizaje (Priority: P2)

**Goal**: An active authenticated account remains on the landing page and sees only one primary action to continue to `/learn/`.

**Independent Test**: Force-login an active account, request `/`, confirm status `200`, find a “Continuar aprendiendo” link to `ui:learner-home`, and confirm the page content excludes the registration and login actions.

### Tests for User Story 2

- [ ] T004 [US2] Add a failing `test_authenticated_account_sees_only_continue_action` case using an active account and exact named destinations in `tests/ui/test_public_landing.py`; run that test alone and confirm it fails before changing the template

### Implementation for User Story 2

- [ ] T005 [US2] Add the `request.user.is_authenticated` action branch in `templates/ui/index.html`, rendering only the shared `button.html` component linked to `ui:learner-home` for authenticated accounts and retaining only registration/login actions for visitors; rerun `tests.ui.test_public_landing` and confirm all US1 and US2 tests pass

**Checkpoint**: Visitor and authenticated landing states are both independently testable and match the clarified action matrix.

---

## Phase 5: User Story 3 - Conservar la protección del aprendizaje (Priority: P3)

**Goal**: The public root does not change active-account protection for `/learn/` or the successful-login destination.

**Independent Test**: Run the existing learner-home tests for anonymous, active and inactive accounts plus the existing successful-login test; all retain their prior redirect and access results.

### Regression Tests for User Story 3

- [ ] T006 [P] [US3] Run `tests.ui.test_learner_home`, `tests.accounts.test_sessions.LogoutAndPrivateSessionTests.test_deactivated_account_loses_private_access`, and `tests.accounts.test_sessions.LoginViewTests.test_valid_login_creates_session_and_redirects_with_303` as specified in `specs/006-public-landing/quickstart.md`, confirming anonymous and inactive accounts remain denied, active accounts retain access, and successful login still returns `303` to `/learn/` without modifying `tests/ui/test_learner_home.py` or `tests/accounts/test_sessions.py`

**Checkpoint**: All three user stories are complete and existing authorization behavior remains unchanged.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Document the public change and verify the complete feature against quality, accessibility and scope gates.

- [ ] T007 [P] Add one concise bullet under `Unreleased` → `Added` in `CHANGELOG.md` stating that `/` now serves the public KronoLearn landing page with account and learning destinations; do not add migration guidance because this feature has no schema or operator migration
- [ ] T008 Execute every automated, browser, product-acceptance, and scope validation in `specs/006-public-landing/quickstart.md`, including the focused tests, anonymous/active/inactive access regressions, login redirect, full `tests.ui` suite, Ruff, Django checks, migration-drift check, keyboard focus, 200% zoom, mobile layout, and the 30-second SC-002 review by the product owner; record acceptance in the feature pull request, run the combined `git diff HEAD --name-only` and `git ls-files --others --exclude-standard` check, and confirm its non-spec output contains only the five implementation paths declared in `specs/006-public-landing/plan.md` while excluding `kronolearn/urls.py` and every other closed path

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup and Foundational (Phases 1-2)**: Already satisfied by the existing codebase.
- **User Story 1 (Phase 3)**: Starts immediately and establishes the route, view and visitor template.
- **User Story 2 (Phase 4)**: Depends on T003 because it extends the same landing template and test module.
- **User Story 3 (Phase 5)**: Has no implementation dependency and may be validated in parallel with US1 or US2; it must pass before final completion.
- **Polish (Phase 6)**: T007 can run after the public behavior is settled; T008 depends on T001-T007.

### User Story Dependencies

- **US1 (P1)**: No dependency; delivers the visitor MVP.
- **US2 (P2)**: Depends on US1's route and template but remains independently verifiable with authenticated state.
- **US3 (P3)**: No code dependency; verifies preserved contracts owned by existing files.

### Task Dependency Graph

```text
T001 → T002 → T003 → T004 → T005 ─┐
T006 [parallel after start] ────────┼→ T008
T007 [parallel after scope fixed] ──┘
```

### Within Each User Story

- Write and run the story test before its implementation task.
- Confirm the expected failure identifies the missing behavior, not an unrelated environment problem.
- Make only the smallest implementation required by the current story.
- Run the focused story tests before crossing its checkpoint.
- Do not modify existing authorization, login or learner-home implementations to make regression tests pass.

### Parallel Opportunities

- T006 is read-only regression validation and can run while T001-T005 are implemented.
- T007 touches only `CHANGELOG.md` and can run in parallel with T006 once the final public behavior is fixed.
- T001-T005 are deliberately sequential because they share `tests/ui/test_public_landing.py` or `templates/ui/index.html` and form two TDD loops.

---

## Parallel Examples

### User Story 1

US1 is a short TDD chain and has no safe internal parallel split:

```text
T001 tests → T002 route/view → T003 visitor template
```

### User Story 2

US2 extends the same test and template files and therefore remains sequential:

```text
T004 authenticated test → T005 authenticated template branch
```

### User Story 3

The preserved-contract suite can run independently while the landing implementation proceeds:

```text
Task: "Run learner-home, inactive-account and successful-login regressions from specs/006-public-landing/quickstart.md"
Parallel with: "Implement US1 or US2 in the new landing files"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T003.
2. Stop and run the US1 independent test.
3. Demonstrate a visitor opening `/`, understanding KronoLearn and reaching registration or login.

### Incremental Delivery

1. **MVP**: T001-T003 deliver the public visitor journey.
2. **Authenticated enhancement**: T004-T005 replace irrelevant account actions with “Continuar aprendiendo”.
3. **Regression gate**: T006 proves `/learn/` and login contracts remain intact.
4. **Release readiness**: T007-T008 document and validate the complete feature.

### Requirement Traceability

| Requirement group | Tasks |
| --- | --- |
| FR-001, FR-002, FR-003, FR-005, FR-008, FR-009 | T001-T003 |
| FR-004 and authenticated clarification | T004-T005 |
| FR-006, FR-007 | T006 |
| FR-010 and release governance | T007-T008 |
| SC-001, SC-003, SC-004, SC-005 | T001-T006, T008 |
| SC-002, SC-006 | T008 |

---

## Notes

- `[P]` tasks use distinct files or perform read-only validation without depending on incomplete changes.
- Story labels provide direct traceability to `spec.md`.
- No task creates a model, service, migration, setting, dependency or client-side state.
- No task modifies `kronolearn/urls.py`, `learner_home`, `ui/templates/base.html`, `accounts`, `learning`, `templates/accounts/` or feature-004 artifacts.
- A task is complete only after its stated verification succeeds.
