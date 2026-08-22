# Data Model: Portada pública de KronoLearn

## Persistence Decision

This feature introduces no domain entities, database tables, migrations, stored content or lifecycle transitions. All landing-page copy is static template content.

## Runtime Inputs

The page consumes only request state already provided by the application:

| Input | Source | Use | Persistence |
| --- | --- | --- | --- |
| Authentication state | Existing server-side session exposed as `request.user.is_authenticated` | Select the appropriate set of navigation actions | None introduced |
| Named route destinations | Existing URL configuration | Build links without hard-coded account workflow URLs | None |

## Derived Presentation State

| State | Visible primary actions | Hidden primary actions |
| --- | --- | --- |
| Visitor | “Crear cuenta”, “Iniciar sesión” | “Continuar aprendiendo” |
| Authenticated account | “Continuar aprendiendo” | “Crear cuenta”, “Iniciar sesión” |

The authenticated action does not grant access. It points to the existing protected learner-home route, whose authorization remains authoritative.

## Validation Rules

- No view or template in this feature imports or queries a model.
- No request value selects a domain object or account identifier.
- No landing-page content is loaded from persistent storage.
- No migration is created or changed.
