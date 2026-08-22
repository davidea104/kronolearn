# Quickstart: Validate the Public Landing Page

## Prerequisites

- Work from branch `006-public-landing` at the repository root.
- Activate the existing virtual environment.
- Use the test settings for portable validation.
- No migration or seed command is required for this feature.

## 1. Run the focused landing tests

```powershell
.\.venv\Scripts\python.exe manage.py test tests.ui.test_public_landing --settings=kronolearn.settings.test -v 2
```

Expected: route resolution, visitor rendering, CTA destinations, authenticated CTA replacement and static-content checks all pass.

## 2. Run preserved access and login contracts

```powershell
.\.venv\Scripts\python.exe manage.py test tests.ui.test_learner_home tests.accounts.test_sessions.LogoutAndPrivateSessionTests.test_deactivated_account_loses_private_access tests.accounts.test_sessions.LoginViewTests.test_valid_login_creates_session_and_redirects_with_303 --settings=kronolearn.settings.test -v 2
```

Expected: anonymous and inactive-account access to `/learn/` remains protected, an active account can open it, and successful login returns `303` toward `/learn/`.

## 3. Run the UI suite and static checks

```powershell
.\.venv\Scripts\python.exe manage.py test tests.ui --settings=kronolearn.settings.test -v 2
.\.venv\Scripts\ruff.exe check ui tests\ui
.\.venv\Scripts\ruff.exe format --check ui tests\ui
.\.venv\Scripts\python.exe manage.py check --settings=kronolearn.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=kronolearn.settings.test
```

Expected: all commands exit successfully and migration drift reports no changes.

## 4. Verify the browser flow

Start the development server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/` and verify:

1. Without a session, the page loads successfully and explains KronoLearn.
2. “Crear cuenta” opens `/accounts/register/` and “Iniciar sesión” opens `/accounts/login/`.
3. Tab reaches every primary action with a visible focus outline; Enter activates each link.
4. At 200% browser zoom and a narrow mobile viewport, text and actions remain readable without overlap or horizontal clipping.
5. After signing in, `/` remains visible, shows “Continuar aprendiendo”, and no longer shows the registration or login actions in the page content.
6. “Continuar aprendiendo” opens `/learn/`.

Stop the server after validation.

## 5. Record product acceptance

Present the visitor landing page to the product owner without explaining its content and start a 30-second timer. Acceptance passes only if the product owner identifies both the platform purpose and the “Crear cuenta” and “Iniciar sesión” options before time expires. Record the result in the feature pull request.

## 6. Verify the closed file scope

```powershell
$implementationChanges = @(
    git diff HEAD --name-only
    git ls-files --others --exclude-standard
) | Where-Object { $_ -notlike "specs/006-public-landing/*" } | Sort-Object -Unique
$implementationChanges
```

Expected implementation paths:

```text
CHANGELOG.md
templates/ui/index.html
tests/ui/test_public_landing.py
ui/urls.py
ui/views.py
```

The command includes staged, unstaged and untracked files while excluding this feature's planning artifacts. Its output must contain only the five implementation paths above and must not include `kronolearn/urls.py`, settings, migrations, `ui/templates/base.html`, `templates/accounts/`, `accounts/`, `learning/`, the implementation of `learner_home` or frozen feature-004 artifacts.

## Contract Reference

See [contracts/public-landing.md](contracts/public-landing.md) for the route, content, action and preserved-regression contracts. See [data-model.md](data-model.md) for the explicit no-persistence design.
