---

description: "Implementation tasks for enrollment exploration and sign-up"
---

# Tasks: Exploración e inscripción en tracks

**Input**: Design documents from `specs/008-enrollment-tracks/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/enrollment.md](contracts/enrollment.md), [quickstart.md](quickstart.md)

**Tests**: Required by the specification's FOCO DE PRUEBAS and by constitution principle 6 (permisos de aprendiz, idempotencia y selección de contenido son de verificación obligatoria). Write each story's test first, confirm the expected failure, implement the smallest change, then rerun the focused command before continuing.

**Organization**: Tasks are grouped by user story and preserve the closed implementation file list from `plan.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and has no dependency on incomplete work.
- **[Story]**: Maps the task to a user story from `spec.md`.
- Every task names the exact file it changes or validates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing project already supplies everything this feature depends on.

No setup task is required. `learning` (app, reserved `learning/urls/enrollment.py`, and `learning/views/__init__.py`), `catalog.services.queries`, `accounts.security.active_account_required`, and `templates/ui/components/` already exist unchanged.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Identify shared infrastructure required before user-story work.

No foundational implementation is required. `learning.Enrollment` and its unique constraint `learning_enrollment_account_track_unique` were created by feature 004; `get_enrollment` and `list_enrollments` are already implemented in `learning/services/enrollment.py` and remain unchanged.

**Checkpoint**: Existing foundation is ready; begin User Story 1.

---

## Phase 3: User Story 1 - Explorar el catálogo de tracks disponibles (Priority: P1) 🎯 MVP

**Goal**: An authenticated learner can see available tracks with title, description, and module count, and open the detail of each.

**Independent Test**: An authenticated learner opens the catalog, sees available tracks with their basic data, and opens the detail of one without enrolling.

### Tests for User Story 1

- [ ] T001 [US1] Create failing `test_list_shows_active_tracks_with_module_count`, `test_list_excludes_retired_tracks`, `test_detail_shows_full_track_information`, and `test_anonymous_redirected_to_login` cases in `tests/learning/enrollment/test_enrollment_views.py`, covering `learning:enrollment-list` and `learning:enrollment-detail`, title/description/module-count presence, exclusion of a retired track, and the anonymous redirect with `next`; run `manage.py test tests.learning.enrollment --settings=kronolearn.settings.test -v 2` and confirm failure before implementation

### Implementation for User Story 1

- [ ] T002 [US1] Add `enrollment_list(request)` and `enrollment_detail(request, track_id)` in `learning/views/enrollment.py`, both decorated with `active_account_required` and `require_http_methods(["GET"])`, consuming only `catalog.services.queries.list_active_tracks`/`get_active_track` for tracks and `learning.services.enrollment.get_enrollment` for the `is_enrolled` flag (module count via `get_active_track(track.id).active_modules` per `research.md`); register `path("", enrollment_list, name="enrollment-list")` and `path("tracks/<str:track_id>/", enrollment_detail, name="enrollment-detail")` in `learning/urls/enrollment.py`; add the `learning-enrollment` `NavItem` (`order=10`) pointing at `learning:enrollment-list` in `learning/nav.py`
- [ ] T003 [US1] Create `templates/learning/enrollment/list.html` and `templates/learning/enrollment/detail.html`, extending `base.html` and reusing `ui/components/card.html`, `ui/components/button.html`, and `ui/components/empty_state.html` per `contracts/enrollment.md`; rerun `tests.learning.enrollment` and confirm all US1 tests pass

**Checkpoint**: The catalog exploration flow is independently functional and is the MVP.

---

## Phase 4: User Story 2 - Inscribirse en un track (Priority: P1)

**Goal**: An authenticated learner can enroll in an available track, with at most one enrollment per account-track pair.

**Independent Test**: A learner submits enrollment for an available track and is registered as enrolled, verifiable only through their own enrollments.

### Tests for User Story 2

- [ ] T004 [US2] Add failing `test_enroll_creates_exactly_one_enrollment`, `test_sequential_double_submit_stays_single_enrollment`, `test_two_accounts_enroll_independently`, `test_htmx_enroll_returns_track_card_partial`, `test_anonymous_enroll_redirected_to_login`, `test_account_cannot_see_another_accounts_enrollment_status`, and `test_spoofed_account_field_in_enroll_post_is_ignored` cases in `tests/learning/enrollment/test_enrollment_views.py`, covering `POST learning:enrollment-enroll`, the row count in `learning.services.enrollment.list_enrollments`, a second sequential submission, isolation between two learner accounts (both for the created rows and for `is_enrolled` visibility on `learning:enrollment-list`/`-detail`), the `HX-Request` fragment vs. the `303` redirect for a plain submission, the anonymous-POST redirect to login with `next`, and that an extraneous account/user-identifying POST field has no effect (FR-009, FR-010, FR-011); run the focused test command and confirm failure before implementation

### Implementation for User Story 2

- [ ] T005 [US2] Implement `enroll(account, track)` in `learning/services/enrollment.py`: attempt `Enrollment.objects.create(...)` inside `transaction.atomic()` and, on `IntegrityError` from `learning_enrollment_account_track_unique`, return the existing row via `get_enrollment(account, track)` instead of raising or duplicating; add `enrollment_enroll(request, track_id)` in `learning/views/enrollment.py` (`active_account_required`, `require_POST`) that resolves the track via `get_active_track`, calls `enroll`, and returns the `track_card.html` fragment for `HX-Request` or an `HttpResponseSeeOther` to `learning:enrollment-detail` otherwise; register `path("tracks/<str:track_id>/enroll/", enrollment_enroll, name="enrollment-enroll")` in `learning/urls/enrollment.py`
- [ ] T006 [US2] Create `templates/learning/enrollment/partials/track_card.html` as the HTMX swap target (`id="track-card-{{ track.id }}"`) with its enrolled (icon + text, never color-only) and not-enrolled (`POST` form with `hx-post`/`hx-target`/`hx-swap="outerHTML"` and the `button.html` submit) states, and include it from `list.html` and `detail.html`; rerun `tests.learning.enrollment` and confirm all US1 and US2 tests pass

**Checkpoint**: Learners can explore and enroll; both P1 stories are independently testable and deliver the MVP together.

---

## Phase 5: User Story 3 - Rechazo uniforme ante tracks no disponibles (Priority: P2)

**Goal**: A retired track and a nonexistent track identifier produce the identical rejection response on both detail and enroll routes, and neither creates an enrollment.

**Independent Test**: A learner requests the detail and the enroll route for a retired track and, separately, for a nonexistent identifier; all four requests return the same response and none creates an enrollment.

### Tests for User Story 3

- [ ] T007 [US3] Add failing `test_retired_and_nonexistent_track_detail_return_identical_rejection` and `test_retired_and_nonexistent_track_enroll_return_identical_rejection_without_enrolling` cases in `tests/learning/enrollment/test_enrollment_views.py`, asserting byte-identical status and body between a retired track and a nonexistent UUID on both `learning:enrollment-detail` and `learning:enrollment-enroll`, and asserting no `Enrollment` row is created by either enroll attempt; run the focused test command and confirm failure, then verify `enrollment_detail`/`enrollment_enroll` in `learning/views/enrollment.py` already return the shared generic `HttpResponseNotFound` message for both cases (adjust only if the assertions reveal a divergence) and rerun until all tests in `tests.learning.enrollment` pass

**Checkpoint**: All three user stories pass; the full enrollment flow is complete and independently verifiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature against the quickstart, quality, and scope gates.

- [ ] T008 Execute every command in `specs/008-enrollment-tracks/quickstart.md`: the focused `tests.learning.enrollment` suite, the full `tests.learning` suite, `ruff check .`, `ruff format --check .`, and `manage.py makemigrations --check --dry-run`; then run `git diff HEAD --name-only` and `git ls-files --others --exclude-standard` and confirm their combined non-spec output contains only the closed implementation file list declared in `specs/008-enrollment-tracks/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup and Foundational (Phases 1-2)**: Already satisfied by the existing codebase.
- **User Story 1 (Phase 3)**: Starts immediately; establishes the routes, views, and templates that User Story 2 extends.
- **User Story 2 (Phase 4)**: Depends on T002-T003 because it adds the enroll route to the same `learning/urls/enrollment.py`/`learning/views/enrollment.py` files and swaps the same templates.
- **User Story 3 (Phase 5)**: Depends on T002 and T005 because it verifies behavior already implemented by `enrollment_detail` and `enrollment_enroll`; it adds no new production code unless a divergence is found.
- **Polish (Phase 6)**: T008 depends on T001-T007.

### User Story Dependencies

- **US1 (P1)**: No dependency; delivers the catalog exploration MVP.
- **US2 (P1)**: Depends on US1's routes and templates; independently verifiable once its own tests pass.
- **US3 (P2)**: Depends on US1's and US2's generic-rejection design; verifies a contract already implied by both, so it carries no independent implementation risk.

### Task Dependency Graph

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008
```

### Within Each User Story

- Write and run the story test before its implementation task.
- Confirm the expected failure identifies the missing behavior, not an unrelated environment problem.
- Make only the smallest implementation required by the current story.
- Run the focused story tests before crossing its checkpoint.

### Parallel Opportunities

- All tasks share `learning/views/enrollment.py`, `learning/urls/enrollment.py`, or `tests/learning/enrollment/test_enrollment_views.py`, so this feature has no safe parallel split; the chain above is deliberately sequential.

---

## Parallel Examples

This feature is a short sequential TDD chain with no independent-file split:

```text
T001 tests → T002 views/urls/nav → T003 templates → T004 tests → T005 service/view/route → T006 partial → T007 tests → T008 polish
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete T001-T003 (exploration) and T004-T006 (enrollment); both are P1.
2. Stop and run the combined independent tests for US1 and US2.
3. Demonstrate a learner exploring the catalog and enrolling exactly once in a track.

### Incremental Delivery

1. **MVP**: T001-T006 deliver the full explore-and-enroll journey.
2. **Robustness gate**: T007 proves the generic rejection contract for retired and nonexistent tracks.
3. **Release readiness**: T008 validates the complete feature against lint, migrations, and the closed file list.

### Requirement Traceability

| Requirement group | Tasks |
| --- | --- |
| FR-001, FR-002 | T001-T003 |
| FR-003, FR-004, FR-005 | T004-T006 |
| FR-006, FR-007, FR-008 | T002, T005, T007 |
| FR-009, FR-010, FR-011 | T001, T004, T007 |
| SC-001 | T001-T003 |
| SC-002 | T004-T006 |
| SC-003 | T007 |
| SC-004 | T001, T004, T007 |
| SC-005 | T008 (manual walkthrough via `quickstart.md`; no automated step-count assertion) |

---

## Notes

- Story labels provide direct traceability to `spec.md`.
- No task modifies `kronolearn/urls.py`, `learning/urls/__init__.py`, `templates/base.html`, or any `catalog` file; `plan.md` lists these as explicitly closed.
- No task adds a migration; `learning.Enrollment` and its unique constraint already exist.
- `learning/views/enrollment.py` MUST define its own generic-not-found message constant and MUST NOT import `catalog.views.GENERIC_NOT_FOUND` or any other symbol from `catalog/views.py`; see the note in `contracts/enrollment.md`.
- SC-005 (three-step explore-to-enroll flow) is verified only through the manual `quickstart.md` scenario executed in T008; this is an accepted manual gate, not an automated task-level assertion.
