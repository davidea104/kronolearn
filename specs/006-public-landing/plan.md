# Implementation Plan: Portada pública de KronoLearn

**Branch**: `006-public-landing` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-public-landing/spec.md`

## Summary

Añadir la portada pública en `/` mediante una ruta `ui:index`, una vista de solo renderizado y una plantilla estática en la raíz de plantillas del proyecto. La plantilla extiende la base existente, reutiliza los componentes visuales publicados y muestra enlaces de registro e inicio de sesión a visitantes o una única acción hacia `ui:learner-home` a cuentas autenticadas, sin consultar modelos ni modificar los contratos existentes de autenticación y acceso a `/learn/`.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17; plantillas Django server-rendered; componentes existentes de `templates/ui/components/`

**Storage**: N/A; la portada usa texto estático y no consulta ni persiste datos

**Testing**: Django `TestCase`/`SimpleTestCase` con `manage.py test`; Ruff 0.16.3 para lint y formato; revisión de aceptación del responsable del producto para SC-002

**Target Platform**: Aplicación web server-rendered desplegada en Linux mediante la infraestructura existente

**Project Type**: Monolito web modular Django

**Performance Goals**: Resolver y renderizar la portada en una sola solicitud, sin operaciones de dominio, consultas explícitas a modelos ni dependencias externas nuevas

**Constraints**: `/` responde `200` y resuelve como `ui:index`; `/learn/` y el redirect de login permanecen intactos; interfaz operable por teclado; contenido estático; sin migraciones, cambios de settings ni nuevas dependencias

**Scale/Scope**: Una ruta, una vista de renderizado, una plantilla pública, un archivo de pruebas UI y una entrada de changelog; tres acciones de navegación existentes distribuidas por estado de autenticación

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design gate: PASS with one constitution-required scope correction.**

- **Principle 1 - Specification-first**: PASS. `spec.md` está validada y las aclaraciones sobre acciones autenticadas y aceptación de la comprensión quedaron resueltas antes de actualizar el plan.
- **Principle 2 - Domain authority**: PASS. La feature no introduce reglas de negocio; la vista solo renderiza y la plantilla solo presenta enlaces existentes.
- **Principles 4 and 12 - Security and authorization**: PASS. La portada es pública y no reemplaza ni reimplementa `active_account_required`; `/learn/` conserva su control autoritativo.
- **Principle 6 - Mandatory verification**: PASS. El plan cubre resolución, respuesta pública, contenido por estado de autenticación y las regresiones de acceso anónimo, cuenta inactiva y activa a `/learn/`, además del redirect de login.
- **Principles 7 and release governance**: PASS after scope correction. Cambiar `/` de `Resolver404` a `200` altera comportamiento público, por lo que `CHANGELOG.md` se añade al alcance cerrado. No hay migración ni guía de migración aplicable.
- **Principles 8 and 9 - Modular, incremental delivery**: PASS. El cambio permanece dentro de `ui`, reutiliza contratos existentes y no añade infraestructura.
- **Principle 11 - Server-rendered and accessible UI**: PASS. La plantilla extiende `base.html`, reutiliza `button.html`, mantiene foco visible, áreas de toque y significado textual, y no añade estado de dominio en cliente.
- **Principle 13 - Privacy minimization**: PASS. El contenido es público y estático; no presenta ni registra datos personales.
- **Principle 16 - File ownership**: PASS after declaring the final closed list below. No hay migraciones y no se modifica ningún archivo congelado por la feature 004.

**Post-design gate: PASS.** `research.md`, `data-model.md`, `contracts/public-landing.md` y `quickstart.md` mantienen el diseño sin datos persistidos, sin servicios nuevos, sin cambios de autorización y dentro de la lista cerrada. La guía ejecuta la regresión de cuenta inactiva, incluye la revisión de aceptación de SC-002 y comprueba archivos rastreados y nuevos sin ampliar el producto.

## Project Structure

### Documentation (this feature)

```text
specs/006-public-landing/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── public-landing.md # Phase 1 UI and routing contract
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ui/
├── urls.py               # Add only the empty-path ui:index route
└── views.py              # Add only the public index render view

templates/
└── ui/
    └── index.html        # Create the static landing page using shared components

tests/
└── ui/
    └── test_public_landing.py  # Route, rendering, CTA, accessibility and regression contracts

CHANGELOG.md              # Record the new public root page as constitutionally required
```

**Structure Decision**: Mantener el monolito y la app `ui` existentes. La vista `index` no recibe servicios ni contexto de dominio; `request.user.is_authenticated`, ya disponible en la plantilla base, selecciona entre los CTA públicos y el CTA autenticado. La plantilla vive en `templates/ui/` como exige el alcance y reutiliza `templates/ui/components/button.html`; no se modifica `ui/templates/base.html` ni se crea CSS o JavaScript separado.

**Closed implementation file list**:

- `ui/urls.py`
- `ui/views.py` (solo añadir `index`; `learner_home` y `components_showroom` permanecen intactas)
- `templates/ui/index.html`
- `tests/ui/test_public_landing.py`
- `CHANGELOG.md` (única corrección al Bloque B, exigida por la constitución)

**Explicitly closed**: `kronolearn/urls.py`, settings, migraciones, `ui/templates/base.html`, `templates/accounts/`, la app `accounts`, la app `learning`, la vista `learner_home` y todos los artefactos congelados de la feature 004.

## Complexity Tracking

No hay violaciones constitucionales ni complejidad adicional que justificar. La inclusión de `CHANGELOG.md` corrige el alcance para cumplir una obligación superior y no introduce arquitectura ni comportamiento adicional.
