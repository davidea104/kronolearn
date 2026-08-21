# Web Contract: Authentication and Profile

<!-- markdownlint-disable MD060 -->

**Date**: 2026-08-20
**Style**: Server-rendered HTML over HTTPS in production
**Data model**: [../data-model.md](../data-model.md)

## Global Rules

- All state-changing operations use POST and require a valid CSRF token.
- Successful POST operations use `303 See Other` to prevent form resubmission.
- Form validation failures return `200 OK` with field errors; submitted passwords are never echoed.
- Anonymous access to private GET routes returns `302 Found` to `/accounts/login/?next=<internal-path>`.
- Authenticated but unauthorized role-management access returns `403 Forbidden` with no target-account details.
- Every authenticated assign/revoke request creates exactly one audit row before its response, including denied, self-target, nonexistent-target and malformed-target outcomes. Anonymous requests stop at the authentication boundary and do not invoke the service.
- Login failures use the same generic text and form shape for wrong password, unknown email, inactive account and an active throttle delay.
- `next` is accepted only when it is same-origin, resolves to an allowlisted private route and the authenticated actor is authorized. Otherwise redirect to `/learn/`.
- HTML forms have explicit labels, associated errors, keyboard-operable controls and an error summary. JavaScript is not required for completion.
- Responses never include password hashes, permission internals, raw throttle digests, session identifiers or role-audit details outside authorized admin views.

## Route Summary

| Name | Method | Path | Access | Success |
|------|--------|------|--------|---------|
| `accounts:register` | GET, POST | `/accounts/register/` | Anonymous | `303` to login after creation |
| `accounts:login` | GET, POST | `/accounts/login/` | Anonymous | `303` to safe `next` or learner home |
| `accounts:logout` | POST | `/accounts/logout/` | Any session state | `303` to login |
| `accounts:profile` | GET, POST | `/accounts/profile/` | Authenticated | `200` view or `303` after update |
| `accounts:role-management` | GET | `/accounts/platform/roles/` | Platform administrator | `200` account-role list |
| `accounts:assign-content-role` | POST | `/accounts/platform/roles/<str:target_ref>/assign/` | Authenticated; service parses and authorizes | `303` to role management |
| `accounts:revoke-content-role` | POST | `/accounts/platform/roles/<str:target_ref>/revoke/` | Authenticated; service parses and authorizes | `303` to role management |
| `ui:learner-home` | GET | `/learn/` | Authenticated | `200` learner start |

## Registration

### GET `/accounts/register/`

Returns the registration form with:

- `email` (`type=email`, autocomplete `email`)
- `display_name` (max 100)
- `password1` (`type=password`, autocomplete `new-password`, max 128)
- `password2` (`type=password`, autocomplete `new-password`, max 128)
- CSRF token

### POST `/accounts/register/`

Input uses the same fields. Server behavior:

1. Call `accounts.security.canonicalize_account_email()` (`raw.strip().casefold()`), then validate email format; trim display name.
2. Validate email shape, display-name length, password confirmation and all configured password validators.
3. Create Account plus `learner` group membership atomically.
4. On a concurrent unique conflict, let the registration transaction roll back and translate `IntegrityError` outside the atomic block. Do not retry account creation; return the exact status, form shape and generic message used for a duplicate found before insertion.

| Condition | Status | Observable result |
|-----------|--------|-------------------|
| Valid new account | `303` | Redirect to login with a neutral account-created message. |
| Missing/invalid input | `200` | Field errors; no Account row. |
| Existing canonical email | `200` | Generic inability-to-register message; no indication of account state or roles. |
| Concurrent duplicate | `200` | Same response as existing canonical email; at most one Account exists. |

The route does not authenticate automatically. The user completes the explicit login flow required by the specification.

## Login

### GET `/accounts/login/`

Returns fields `username` labelled as correo electronico, `password`, optional hidden `next`, and CSRF token. Password managers and paste remain supported.

### POST `/accounts/login/`

1. Canonicalize declared email with `canonicalize_account_email()` and derive HMAC account/origin keys.
2. If either bucket is blocked, do not evaluate credentials; return the generic failure with `Retry-After` equal to the remaining whole seconds.
3. Otherwise authenticate through Django's `ModelBackend`.
4. Invalid credentials update both buckets and return the generic failure.
5. Valid credentials clear the account bucket, rotate/create the session, validate `next` and return `303`.

| Condition | Status | Observable result |
|-----------|--------|-------------------|
| Valid active account | `303` | Safe internal destination or `/learn/`. |
| Invalid, unknown or inactive account | `200` | `No fue posible iniciar sesion con los datos proporcionados.` |
| Active progressive delay | `429` | Same generic message plus `Retry-After`; no credential evaluation. |
| External/malformed/unauthorized `next` after valid login | `303` | `/learn/`; supplied destination is not reflected into output. |

Account-existence variants follow equivalent authentication work and identical response content within the same throttle state.

## Logout

### POST `/accounts/logout/`

- Requires CSRF.
- Calls Django `logout()` and clears the current session.
- Returns `303` to `/accounts/login/` whether the request began authenticated or already logged out.
- GET is not supported and returns `405 Method Not Allowed`.

## Own Profile

### GET `/accounts/profile/`

Returns only the current `request.user` projection:

- canonical email (read-only)
- display name
- derived role labels

The path has no account identifier and performs no arbitrary account lookup. Query parameters such as `account_id` or `user_id` are ignored and never influence the account projection.

### POST `/accounts/profile/`

Accepts only `display_name` and CSRF token.

| Condition | Status | Observable result |
|-----------|--------|-------------------|
| Valid display name | `303` | Redirect to own profile; email, password and roles unchanged. |
| Empty or over 100 characters | `200` | Validation error; no fields changed. |
| Extra fields (`account_id`, `user_id`, `email`, `groups`, `is_superuser`, `password`) with valid `display_name` | `303` | Extra fields are discarded before form validation; only the current session account's `display_name` changes. |
| Extra fields with invalid `display_name` | `200` | Only the `display_name` error is returned; no fields change. |

## Learner Home

### GET `/learn/`

Minimal destination for an active account with a valid authenticated session. It identifies the signed-in learner and provides navigation to profile and logout. A deactivated account's existing session is logged out and redirected to login with the same generic account-state handling used elsewhere. Educational catalog/session functionality remains out of scope.

## Platform Role Management

### GET `/accounts/platform/roles/`

- Requires an active `is_superuser` account.
- Returns a paginated list of accounts with UUID, canonical email, display name and derived roles.
- Optional `q` filters canonical email/display name through parameterized Django ORM `icontains` queries; input is length-limited and output is template-escaped.
- Role audit is not exposed to learners or content administrators. Platform administrators review it read-only through Django admin.

### POST assign/revoke

Both routes accept only CSRF. The requested target reference comes from one non-empty path segment captured as a string; actor always comes from `request.user`. The view requires authentication but does not parse UUIDs, resolve accounts or perform a superuser short-circuit: parsing, authorization and audit are one service operation so every authenticated attempt reaches exactly one terminal result. The raw reference is never copied into responses, logs or database fields.

| Actor/target condition | Status | Mutation | Audit |
|------------------------|--------|----------|-------|
| Platform admin, existing target, membership changes | `303` | Add/remove only `content_admin`; preserve `learner` | One `SUCCESS`, `changed=True` |
| Platform admin, existing target, membership already desired | `303` | No change | One `SUCCESS`, `changed=False` |
| Platform admin, same actor and target | `403` | No change | One `DENIED` associated with that account, `changed=False` |
| Learner/content admin, existing target | `403` | No change | One `DENIED`, `changed=False` |
| Platform admin, target UUID not found | `404` | No change | One `TARGET_NOT_FOUND`, `target=null`, non-reversible `requested_target_digest`, `changed=False` |
| Learner/content admin, target UUID not found | `403` | No change; response does not reveal target existence | One `TARGET_NOT_FOUND`, `target=null`, non-reversible `requested_target_digest`, `changed=False` |
| Platform admin, target reference has invalid UUID format | `404` | No change | One `TARGET_NOT_FOUND`, `target=null`, non-reversible `requested_target_digest`, `changed=False` |
| Learner/content admin, target reference has invalid UUID format | `403` | No change; response matches other unauthorized attempts | One `TARGET_NOT_FOUND`, `target=null`, non-reversible `requested_target_digest`, `changed=False` |
| Anonymous actor | `302` | No change | No role-service invocation; redirect to login |

The service attempts UUID parsing and, if valid, account resolution. It signs the canonical UUID for a nonexistent target or the decoded path segment for an invalid reference using the dedicated role-audit HMAC purpose; neither value is persisted in clear text. It then evaluates permission and actor/target separation before every mutation. The HTTP layer maps the service result without changing or duplicating the audit: `TARGET_NOT_FOUND` is distinguishable as `404` only to a platform administrator and is the generic unauthorized `403` for every other authenticated actor. Template visibility is convenience only and never an authorization control.

## Safe Return Route Policy

Initial allowlist:

| Route name | Authorization predicate |
|------------|-------------------------|
| `ui:learner-home` | Active authenticated account |
| `accounts:profile` | Active authenticated account |
| `accounts:role-management` | Active platform administrator |

Assign/revoke POST routes are never return destinations. Future private GET routes must register an explicit predicate before they can be accepted as `next`.

`accounts.security.resolve_safe_next()` owns an immutable mapping from URL names to authorization predicate callables. It accepts only same-origin candidates that resolve to an allowlisted GET route and whose predicate passes for the authenticated active actor; it never infers safety from path prefixes or template visibility.

## Security Event Logging

Application logs emit structured event names without secrets or direct email/IP values:

- `accounts.login.succeeded`
- `accounts.login.failed`
- `accounts.login.throttled`
- `accounts.role_change.succeeded`
- `accounts.role_change.denied`
- `accounts.role_change.target_not_found`

Fields are limited to event timestamp, account UUID when authenticated, pseudonymous digests, action/result and request correlation identifier. Passwords, cookies, session keys, CSRF tokens and raw credentials are prohibited.

## Contract Test Matrix

| Requirement | Contract checks |
|-------------|-----------------|
| FR-001..004 | Registration fields, validation, atomic learner assignment, canonical uniqueness and concurrency. |
| FR-005..006 | Generic login failures, valid session, POST-only idempotent logout and session invalidation. |
| FR-007 | Anonymous redirect, safe `next`, fallback and destination authorization. |
| FR-008..010, FR-013 | Two-session current-user-only profile, ignored account identifiers and ignored privilege fields. |
| FR-011..012 | Superuser-only cumulative role mutation, self-target denial and unauthorized denial without changes. |
| FR-014 | Dual-scope progressive delay, cap, reset window and account-existence parity. |
| FR-015 | Exactly one complete immutable audit record per authenticated role attempt, using a target relation when resolved or a non-reversible requested-target digest when the UUID is nonexistent or malformed; only platform administrators observe the not-found distinction. |
