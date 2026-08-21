# Validation Evidence

Validation date: 2026-08-21.

## Environment

- Windows, Python 3.13.14, Django 5.2.17, Ruff 0.16.3.
- Fast suite: Django test settings with SQLite in memory.
- Authoritative database suite: disposable PostgreSQL 16.11 cluster bound only to loopback with local temporary storage.
- Python 3.14 remains the authoritative CI/runtime version; local Python 3.13.14 results are supporting evidence.

No credentials, request payloads, participant data, or unresolved raw references are recorded here. The disposable PostgreSQL clusters, password files, logs, browser fixtures, and validation servers were removed after execution.

## Automated Gates

- `ruff check .`: passed.
- `ruff format --check .`: 123 files already formatted.
- `python manage.py check --settings=kronolearn.settings.test`: passed with no issues.
- `python manage.py makemigrations --check --dry-run --settings=kronolearn.settings.test`: no changes detected.
- `python manage.py test tests.accounts tests.catalog tests.smoke tests.ui --settings=kronolearn.settings.test -v 1`: 156 tests passed, 9 PostgreSQL/environment-specific tests skipped.
- `git diff --check`: passed.

## PostgreSQL 16 Gates

Environment: disposable PostgreSQL 16.11 cluster on loopback port 55441. The test role owned its database and could create and destroy Django test databases.

- `python manage.py test tests.catalog --settings=kronolearn.settings.development -v 1`: 77 tests passed with no skips in 48.350 seconds.
- `python manage.py test --settings=kronolearn.settings.development -v 1`: 157 tests passed with no skips in 132.485 seconds.
- `python -m unittest tests.db.test_db_connection -v`: 1 test passed in 0.045 seconds.
- PostgreSQL concurrency coverage used `TransactionTestCase`, independent connections, and real row locks for track/module ordering and publication.
- SC-008 passed separately with 200 observations and aggregate p95 0.2363932301 seconds; see `performance.md`.
- Cleanup verified no listener on ports 55441, 55442, or 8765 and no remaining database cluster, browser fixture, log, password, or wrapper files.

## Functional Scenarios

The ten quickstart scenarios were executed through the server-rendered views and transactional services. The test methods below are the reproducible acceptance record; browser checks supplement the HTMX and learner-return paths. This is not the pending internal three-participant acceptance tracked by T041.

| Scenario | Executed coverage | Result |
| -------- | ----------------- | ------ |
| 1. Inactive structure | `test_create_track_normalizes_and_appends_atomically`, `test_create_track_rejects_blank_overlong_and_duplicate_normalized_title`, `test_create_module_derives_parent_appends_and_scopes_title_uniqueness` | Passed |
| 2. Validation and protected fields | `test_create_track_uses_prg_and_ignores_protected_fields`, `test_module_create_uses_parent_from_url_and_prg`, `test_publication_source_is_free_text_trimmed_and_bounded` | Passed |
| 3. Publish module and track | `test_activation_validates_metadata_and_requires_active_module`, `test_activation_reactivation_and_current_noop_version_correctly`, `test_module_activation_reactivation_noop_and_stale_revision` | Passed |
| 4. Edit active and inactive content | `test_active_edit_publishes_but_inactive_edit_does_not`, `test_active_edit_without_metadata_preserves_content_and_version`, `test_module_edit_keeps_parent_position_and_versions_only_when_active`, `test_active_module_edit_without_metadata_preserves_content_and_version` | Passed |
| 5. Reorder tracks and modules | Ordering service tests plus HTMX success, invalid, stale-token, and retry tests in `test_admin_views`; real browser confirmed HTMX 2.0.7 with SHA-384 SRI, allowlisted targets, fragment-only 200/409 responses, HTML/CSRF fallback, stable URL, accessible success status, current revision after conflict, successful retry, and preserved order on errors | Passed |
| 6. Administrator conflicts | PostgreSQL concurrency tests for track/module edits and ordering, stale state tests, and HTMX 409 tests | Passed |
| 7. Learner catalog | `test_list_and_detail_show_only_active_hierarchy`, `test_module_detail_validates_parent_and_active_state`, `test_malformed_references_use_the_same_generic_404`, `test_malformed_catalog_next_falls_back`, `test_invalid_admin_object_next_falls_back`; browser confirmed malformed direct access returns only the generic 404 and malformed learner or administrative `next` falls back to `/learn/` | Passed |
| 8. Deactivation invariants | `test_last_active_module_of_active_track_cannot_be_deactivated`, `test_deactivating_module_with_replacement_preserves_positions`, `test_deactivating_track_preserves_module_states_and_positions` | Passed |
| 9. Authorization and CSRF | `test_track_list_requires_content_admin_role`, `test_learner_post_reaching_service_is_denied_once_without_disclosure`, `test_mutation_without_csrf_stops_before_service`, `test_state_and_reorder_routes_reject_get`, account safe-return tests | Passed |
| 10. Audit and immutability | Outcome, unresolved-reference digest, immutable model, mutually exclusive reference, and read-only admin tests across `test_content_services`, `test_models`, and `test_admin` | Passed |

## Contract Corrections Found During Validation

- Learner URL converters previously returned Django's technical 404 page for malformed UUIDs instead of the same generic body used for hidden content. Learner references now enter as opaque strings and are parsed inside authorized query helpers.
- A malformed learner catalog URL supplied as login `next` previously raised UUID `ValidationError`. Safe-return authorization now reuses the same active catalog query helpers and falls back to `/learn/`.
- Dynamic administrative login destinations previously checked only the `content_admin` role. Safe-return authorization now also resolves the referenced track/module through authorized query helpers, including parent-child consistency, and falls back to `/learn/` for malformed or missing objects.
- The pinned HTMX client now carries verified SHA-384 SRI and anonymous CORS metadata. Successful track/module swaps announce `Orden actualizado.` through `role="status"`; conflict fragments carry the current revision so a retry can succeed without a full reload.
- Regression tests cover these paths, and the web contract documents the opaque learner string converters.

## Remaining Human Gate

T041 remains pending. Its internal manual acceptance requires three team members using separate disposable content-administrator accounts, including a controlled stale-revision collision and retry. It cannot be inferred from automated tests or agent-driven browser execution; see `usability.md`.
