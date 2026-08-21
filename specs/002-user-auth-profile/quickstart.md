# Quickstart Validation: Autenticacion y perfil

**Purpose**: Validar el feature de extremo a extremo despues de su implementacion.
**Spec**: [spec.md](spec.md)
**Contract**: [contracts/web-auth.md](contracts/web-auth.md)
**Data model**: [data-model.md](data-model.md)

## Prerequisites

- Python 3.14 virtual environment with `requirements.txt` installed.
- Reachable PostgreSQL database dedicated to local development/testing.
- PowerShell from the repository root.
- No production credentials or shared database.

## Environment

Set values for the current PowerShell process:

```powershell
$env:DJANGO_SETTINGS_MODULE = "kronolearn.settings.development"
$env:SECRET_KEY = "local-only-secret-key-change-me"
$env:DEBUG = "True"
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/kronolearn"
```

Install the locked dependencies if needed:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

## Schema and Configuration Checks

### Required initial identity migration

This feature sets `AUTH_USER_MODEL = "accounts.Account"`. That setting and the
`accounts/0001_initial.py` migration must be present before the first migration
is applied to an environment. Django does not support switching an existing
database from its default user model to this custom model in place.

- For a new environment, start with an empty PostgreSQL database and run the
  commands below normally.
- For an environment already migrated with Django's default user model, stop
  and either recreate an empty database or execute a separately reviewed data
  migration plan. Do not deploy this feature over those tables directly.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --noinput
```

Expected:

- `System check identified no issues`.
- No uncommitted model changes.
- `accounts.Account` is the active user model.
- Groups `learner` and `content_admin` exist after migration.

Create the operational platform administrator:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Use a local-only email and a password of at least 15 characters.

## Automated Verification

Run the feature suite first:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.accounts tests.ui -v 2
```

Then run all repository gates:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m unittest tests.db.test_db_connection -v
```

Expected: every command exits `0`. The concurrency tests must run against PostgreSQL, not SQLite.

## Manual End-to-End Validation

Start the development server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/accounts/register/`.

### Scenario 1: Registration and Login

1. Register `learner@example.com`, display name `Learner One`, and a valid password.
2. Confirm registration redirects to login rather than creating a session.
3. Log in with uppercase/spaced email variant where the form permits surrounding whitespace.
4. Confirm redirect to `http://127.0.0.1:8000/learn/`.
5. Open profile and confirm roles show `learner` only.

Expected: one canonical account exists, password is not displayed, and the learner home is private.

### Scenario 2: Duplicate and Invalid Registration

1. Attempt registration with `LEARNER@example.com`.
2. Attempt registration with a missing display name.
3. Attempt registration with a password shorter than 15 characters.

Expected: no additional or partial account is created; errors do not reveal private account state.

### Scenario 3: Profile Isolation

1. Register and sign in as a second learner in a separate private browser session.
2. Visit `/accounts/profile/` in both sessions.
3. Add the other account's UUID as an `account_id` query parameter and confirm the displayed profile does not change.
4. Submit a profile update containing `display_name`, the other account's UUID as `account_id`, and crafted fields such as `email`, `groups` or `is_superuser`.

Expected: each session sees and changes only its own profile; additional account identifiers are ignored; email, password and roles remain unchanged.

### Scenario 4: Private Routes and Safe Return

1. Log out and request `/accounts/profile/`.
2. Confirm redirect to login with an internal `next` value.
3. Log in and confirm return to own profile.
4. Repeat with `next=https://example.org/`, malformed input and the platform role-management path as a learner.

Expected: invalid, external or unauthorized destinations fall back to `/learn/`.

### Scenario 5: Progressive Login Delay

1. Submit repeated invalid passwords for an existing email.
2. Repeat with an unknown email and from a second origin available in the test environment.
3. Observe `Retry-After` after the delay activates.
4. Complete a valid login after the applicable delay.

Expected: delays progress from 1 second up to the 60-second cap, response text does not distinguish account existence, and successful login clears the account-scoped bucket.

Automated tests are authoritative for timing and origin simulation; do not wait through every interval manually.

### Scenario 6: Role Assignment and Revocation

1. Sign in as the platform administrator and open `/accounts/platform/roles/`.
2. Assign `content_admin` to `learner@example.com`.
3. Confirm both `learner` and `content_admin` remain visible.
4. Repeat assignment and confirm no duplicate membership.
5. Revoke `content_admin` and confirm `learner` remains.
6. Attempt to assign and revoke `content_admin` on the platform administrator's own account.
7. Attempt the same operations while signed in as a learner and as a content administrator.

Expected: only the platform administrator changes another account's membership; self-target and unauthorized attempts return `403` and never alter roles.

### Scenario 7: Audit Trail

1. In Django admin, open the read-only role change log as the platform administrator.
2. Inspect entries from successful, repeated no-op, unauthorized and self-target denied attempts.
3. Submit an assign or revoke request as the platform administrator using a syntactically valid UUID that does not identify an account; confirm `404`.
4. Submit another request as the platform administrator using a malformed value such as `not-a-uuid`; confirm `404`.
5. Repeat both the nonexistent-target and malformed-target requests as a learner; confirm the same generic `403` used for its other unauthorized role requests.
6. Inspect all four unresolved-target entries and confirm each has `target` empty, result `TARGET_NOT_FOUND`, `changed=False` and a non-empty non-reversible reference that is not the submitted value.
7. Confirm equivalent valid UUID spellings correlate to the same digest after canonicalization, while repeated identical malformed values correlate without exposing their raw text.
8. Try to access change/delete operations for an audit entry.

Expected: every authenticated attempt has exactly one row with actor, action, result, changed flag and timestamp; existing targets use the account relation, nonexistent or malformed targets use only the non-reversible reference, only the platform administrator receives the not-found distinction, and no update/delete interface is available.

### Scenario 8: Logout

1. Submit logout from an authenticated session.
2. Request `/accounts/profile/` with the same browser.
3. Submit logout again from the unauthenticated state.
4. Request logout with GET.

Expected: the session cannot reopen private routes, repeated POST is safe, and GET returns `405`.

### Scenario 9: Representative Acceptance Protocol

1. Recruit ten participants representative of the intended learner audience who have not been coached through the flow.
2. Give each participant valid, non-production registration data and present the registration page without procedural instructions.
3. Start timing when the participant sees the form and stop when the first authenticated learner home appears.
4. Ask the participant to close the session and identify, without assistance, when the interface is signed in and when it is signed out.
5. Record only elapsed seconds, completion status and whether both states were identified; do not retain credentials, account identifiers or recordings containing private data.
6. Aggregate the ten observations and verify that at least nine participants completed registration and first login in less than 180 seconds and that at least nine identified both session states correctly.

Expected: SC-001 and SC-006 pass over the same ten-person sample. Any assisted run is invalid and must be replaced rather than counted as a success or failure. This protocol does not establish a system latency or load target.

## Database Spot Checks

Use Django shell without printing password hashes, raw session values or throttle keys:

```powershell
.\.venv\Scripts\python.exe manage.py shell
```

Check only safe aggregates and role labels:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import LoginThrottleBucket, RoleChangeLog

Account = get_user_model()
print(Account.objects.count())
print(list(Group.objects.values_list("name", flat=True)))
print(LoginThrottleBucket.objects.values("scope").order_by("scope").distinct())
print(RoleChangeLog.objects.values("action", "result", "changed"))
print(
    RoleChangeLog.objects.filter(target__isnull=True).values(
        "action", "result", "changed"
    )
)
```

Exit with `exit()`.

## Acceptance Evidence

Capture for review:

- CI output with all gates green.
- Automated test names covering each FR group in [contracts/web-auth.md](contracts/web-auth.md#contract-test-matrix).
- Screenshots of registration, learner profile and platform role management using non-sensitive local data.
- Aggregate audit assertions, never raw credentials, session identifiers, email/IP throttle keys or production data.
- An aggregate ten-row acceptance worksheet containing only elapsed time, completion and session-state identification, with at least nine passing rows for SC-001 and SC-006.
