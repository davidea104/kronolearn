# Public Landing Contract

## Route Contract

| Property | Contract |
| --- | --- |
| Method | `GET` |
| Path | `/` |
| Django name | `ui:index` |
| Anonymous response | `200` with the public landing page |
| Authenticated response | `200` with the public landing page |
| Template | `ui/index.html` |
| Persistence | No reads or writes introduced by the landing view |

`resolve("/").view_name` must equal `ui:index`. The route is declared by `ui.urls`; `kronolearn/urls.py` remains unchanged.

## Content Contract

Every successful response contains:

- the product name “KronoLearn”;
- a concise statement of the platform’s learning purpose;
- one level-one heading that identifies the primary page content;
- semantic links whose destinations are generated from existing named routes.

The page does not contain blog, pricing, testimonials, a contact form, language selection or database-managed content.

## Action Contract

### Visitor

| Label | Named destination | Required |
| --- | --- | --- |
| Crear cuenta | `accounts:register` | Yes |
| Iniciar sesión | `accounts:login` | Yes |
| Continuar aprendiendo | `ui:learner-home` | No |

### Authenticated account

| Label | Named destination | Required |
| --- | --- | --- |
| Continuar aprendiendo | `ui:learner-home` | Yes |
| Crear cuenta | `accounts:register` | No |
| Iniciar sesión | `accounts:login` | No |

Each primary action is rendered with `ui/components/button.html` inside the landing page's main content. The landing page does not determine whether the authenticated account may enter `/learn/`; the existing destination enforces that contract.

## Preserved Contracts

- Anonymous access to `ui:learner-home` continues to redirect to `accounts:login` and preserves the requested destination.
- Inactive accounts continue to be denied access to `ui:learner-home` by the existing account protection.
- A successful login without another authorized destination continues to return `303` toward `ui:learner-home` (`/learn/`).
- `ui:components-showroom` and `ui:learner-home` retain their current route names and implementations.

## Accessibility Contract

- All primary actions are keyboard focusable and activatable.
- Visible focus is inherited from the shared base and may not be suppressed.
- Action meaning is conveyed by text, not color alone.
- Interactive targets retain the shared minimum size of 44 by 44 pixels.
- At 200% zoom and at the existing mobile breakpoint, content and actions remain readable without overlap or horizontal clipping.

## Product Acceptance Contract

Without prior explanation of the page, the product owner must identify the platform purpose and both visitor access options within 30 seconds. The feature passes SC-002 only when this result is recorded as accepted in the pull request.
