# Shared Integration Surfaces

These files are composed once by feature 004 and are frozen for the six baseline features after merge.

## Root URL Composition

`kronolearn/urls.py` includes each app exactly once at the empty prefix so the app owns its public path:

| Namespace | URL module | App-owned prefixes |
| --- | --- | --- |
| `catalog` | `catalog.urls` | Existing learner and catalog-management routes |
| `learning` | `learning.urls` | `learn/enrollments/`, `learn/session/`, `learn/attempts/`, `learn/progress/` |
| `gamification` | `gamification.urls` | Reserved gamification routes |
| `analytics` | `analytics.urls` | Reserved analytics routes |

`learning.urls` is a package. Its `__init__.py` defines `app_name = "learning"` and includes the four area modules. Each area module owns only its `urlpatterns`; no service or view is re-exported.

Reserved route names used by navigation are:

```text
learning:enrollment-list
learning:session-current
learning:attempt-submit
learning:progress-detail
gamification:leaderboard
analytics:content-metrics
```

Absent leaf routes do not fail application startup; navigation omits names that cannot yet be reversed.

## Base Template Blocks

Canonical template: `ui/templates/base.html`.

| Block | Purpose |
| --- | --- |
| `title` | Document title; already present |
| `main` | Main page region |
| `content` | Compatibility child nested inside `main` for existing templates |
| `sidebar` | Optional complementary region outside main content flow |
| `fragments` | Out-of-flow server-rendered fragments such as dialogs or live regions |
| `scripts` | Page-specific deferred scripts at the end of body |

The base template renders navigation from the context-provided registry and retains semantic `<nav>` and keyboard-visible focus behavior. Feature 004 verifies the rendered structure and applicable focus rules or classes with fast automated template/style assertions; browser automation and manual review are not required. The template contains no domain calculations.

## Navigation Registry

`ui.navigation.NavItem` is a frozen dataclass:

```python
@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    url_name: str
    order: int
    authenticated: bool = True
    required_role: str | None = None
    superuser_only: bool = False
```

Each installed app may expose `NAV_ITEMS: tuple[NavItem, ...]` from `<app>.nav`. Discovery:

1. Iterates installed app configs in configured order.
2. Imports `<app>.nav` when present; absence is not an error.
3. Rejects duplicate keys during system checks.
4. Filters entries from server-side account state.
5. Attempts `reverse(url_name)` and omits unresolved future routes.
6. Sorts by `(order, key)` and returns immutable resolved entries.

The context processor exposes `primary_navigation`. No account identifier is placed in a URL or form by the registry.

## Reserved Directories

The following template directories are tracked with `.gitkeep` until their owning feature adds templates:

```text
templates/catalog/content/
templates/learning/enrollment/
templates/learning/session/
templates/learning/attempts/
templates/learning/progress/
templates/gamification/
templates/analytics/
```

Equivalent Python test packages are reserved at `tests/catalog/content/`, `tests/learning/enrollment/`, `tests/learning/session/`, `tests/learning/attempts/`, `tests/learning/progress/`, `tests/gamification/`, and `tests/analytics/`. `learning/views/__init__.py`, `learning/services/__init__.py`, and all service package initializers remain empty and contain no re-exports.

## Demo Command

```text
python manage.py seed_demo [--confirm-production]
```

- Runs atomically and uses stable natural keys.
- Creates two named tracks, one module per track, one published content item per module, one current version per item, valid choices, one lab per version, one learner, one content admin, and the current weekly season. Demo accounts use deterministic non-personal addresses under the reserved `.invalid` domain as private `Account` natural keys.
- A repeated run preserves logical identities and counts; it may repair an incomplete recognized demo aggregate but never overwrites unrelated records.
- With `DEBUG=False`, absence of `--confirm-production` raises `CommandError` before writes.
- With `DEBUG=False` and confirmation, demo accounts receive unusable passwords.
- Output contains counts and public titles only; it never prints the `.invalid` emails, passwords, tokens, account IDs, or idempotency keys. The demo emails persist only in their authoritative `Account` rows.
