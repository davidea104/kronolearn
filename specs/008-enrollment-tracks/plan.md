# Implementation Plan: Exploración e inscripción en tracks

**Branch**: `008-enrollment-tracks` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-enrollment-tracks/spec.md`

## Summary

Implementar la inscripción del aprendiz dentro de la app `learning`: un listado y un detalle propios de tracks disponibles bajo `learn/enrollments/`, y una acción de inscripción por `POST` con mejora progresiva HTMX. El listado y el detalle consumen exclusivamente los servicios de consulta ya publicados por `catalog` (`list_active_tracks`, `get_active_track`) para filtrar tracks activos, sin reimplementar esa regla ni importar modelos de `catalog`. La inscripción implementa `learning.services.enrollment.enroll` resolviendo la repetición capturando el conflicto de la restricción única de base de datos dentro de una transacción, y reutiliza `get_enrollment` y `list_enrollments`, ya implementados, para conocer y listar el estado de inscripción. Un track retirado y uno inexistente producen la misma respuesta genérica de no encontrado.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17; HTMX para mejora progresiva de formularios POST; componentes existentes de `templates/ui/components/` (`card`, `button`, `empty_state`)

**Storage**: PostgreSQL; reutiliza `learning.Enrollment` ya migrado por la feature 004 (restricción única `account`+`track`); esta feature no añade migraciones

**Testing**: Django `TestCase` vía `manage.py test --settings=kronolearn.settings.test`; Ruff 0.16.3 para lint y formato

**Target Platform**: Aplicación web server-rendered desplegada en Linux mediante la infraestructura existente

**Project Type**: Monolito web modular Django

**Performance Goals**: Cada pantalla resuelve en una sola solicitud; el listado acepta una consulta adicional por track para su conteo de módulos activos (ver Research), aceptable al tamaño de catálogo de la línea base (dos tracks)

**Constraints**: Toda inscripción MUST ser como máximo una por par cuenta-track, garantizada por la restricción única existente y no por una comprobación previa; el rechazo ante track retirado o inexistente MUST ser indistinguible; ninguna pantalla MUST exponer inscripciones ajenas; no se añaden migraciones, señales ni dependencias nuevas

**Scale/Scope**: Dos rutas de lectura (listado, detalle), una ruta de escritura (inscribirse), un servicio de dominio (`enroll`), tres plantillas nuevas bajo `templates/learning/enrollment/`, una entrada de navegación y su suite de pruebas enfocada

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design gate: PASS.**

- **Principle 1 - Specification-first**: PASS. `spec.md` está validada por su checklist de calidad sin marcadores `[NEEDS CLARIFICATION]` pendientes.
- **Principle 2 - Domain authority**: PASS. La decisión de inscribir, la idempotencia y la consulta de estado viven en `learning/services/enrollment.py`; las vistas solo invocan servicios de `learning` y de consulta de `catalog` y presentan el resultado.
- **Principles 4 y 12 - Seguridad y autorización en profundidad**: PASS. Toda ruta exige `active_account_required`; la identidad se toma de `request.user` en el servidor; ningún formulario ni URL transporta un identificador de cuenta ajeno; el rechazo ante track retirado o inexistente es genérico e indistinguible.
- **Principle 5 - Idempotencia e integridad**: PASS. `enroll` resuelve la repetición capturando el conflicto de `learning_enrollment_account_track_unique` dentro de una transacción atómica; no existe comprobación previa que sustituya la restricción de base de datos.
- **Principle 6 - Verificación obligatoria**: PASS. El plan cubre exclusión de tracks inactivos, creación única, doble envío secuencial, respuesta genérica ante track inactivo o inexistente, y aislamiento entre cuentas.
- **Principle 14 - Comunicación entre módulos**: PASS. La feature lee tracks activos únicamente a través de `catalog.services.queries.list_active_tracks` y `get_active_track`; no importa `catalog.models` ni reimplementa el filtro de estado.
- **Principles 8 y 9 - Monolito modular y entrega incremental**: PASS. El cambio permanece dentro de `learning`, reutiliza contratos ya cableados por la feature 004 y no introduce infraestructura nueva.
- **Principle 11 - Frontend server-rendered y accesible**: PASS. Las plantillas extienden `base.html`, reutilizan `card.html`, `button.html` y `empty_state.html`, y siguen el patrón HTMX ya establecido en `templates/catalog/partials/track_rows.html` (formulario `POST` con `hx-post`/`hx-target`/`hx-swap`, funcional sin JavaScript).
- **Principle 13 - Privacidad por minimización**: PASS. Ninguna pantalla ni registro expone identificadores de otra cuenta ni datos sensibles.
- **Principle 16 - Propiedad de archivos y migraciones**: PASS tras declarar la lista cerrada de archivos abajo. No hay migraciones nuevas.

**Post-design gate: PASS.** `research.md`, `data-model.md`, `contracts/enrollment.md` y `quickstart.md` mantienen el diseño dentro de la lista cerrada, sin nuevos modelos, señales ni dependencias, y verifican exclusión de inactivos, unicidad, doble envío, respuesta genérica y aislamiento entre cuentas.

## Project Structure

### Documentation (this feature)

```text
specs/008-enrollment-tracks/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── enrollment.md     # Phase 1 route, service, and template contract
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
learning/
├── services/
│   └── enrollment.py        # Implement enroll(); get_enrollment/list_enrollments stay unchanged
├── views/
│   └── enrollment.py         # New: list, detail, and enroll (POST) view functions
├── urls/
│   └── enrollment.py         # Populate the reserved enrollment-list/-detail/-enroll routes
└── nav.py                    # Add the enrollment listing entry

templates/
└── learning/
    └── enrollment/
        ├── list.html          # Available tracks with module count and enroll action
        ├── detail.html        # Track detail with enroll action
        └── partials/
            └── track_card.html # HTMX swap target shared by list and detail

tests/
└── learning/
    └── enrollment/
        └── test_enrollment_views.py  # Listing, detail, enroll, idempotency, isolation, generic rejection
```

**Structure Decision**: La feature permanece dentro de `learning`, la única app que puede tocar. El listado y el detalle son propios de `learning` (no reutilizan las plantillas de `catalog` porque estas ya están fuera de la lista de archivos permitidos y no muestran conteo de módulos ni acción de inscripción); ambos consumen `catalog.services.queries.list_active_tracks` y `get_active_track` como único punto de lectura de tracks. `learning/services/enrollment.py` implementa `enroll` y conserva las firmas reservadas de `get_enrollment` y `list_enrollments`. Las rutas se registran dentro del paquete ya incluido `learning.urls.enrollment`, bajo el prefijo congelado `learn/enrollments/`.

**Closed implementation file list**:

- `learning/services/enrollment.py` (solo implementar `enroll`; `get_enrollment` y `list_enrollments` permanecen intactas)
- `learning/views/enrollment.py` (nuevo)
- `learning/urls/enrollment.py`
- `learning/nav.py`
- `templates/learning/enrollment/list.html`, `templates/learning/enrollment/detail.html`, `templates/learning/enrollment/partials/track_card.html`
- `tests/learning/enrollment/test_enrollment_views.py`

**Explicitly closed**: `kronolearn/urls.py`, `learning/urls/__init__.py`, `templates/base.html`, cualquier archivo de `catalog` (modelos, vistas, urls o plantillas), y todo lo creado en la feature 004 fuera de los archivos listados arriba. No se añaden migraciones.

## Complexity Tracking

No hay violaciones constitucionales ni complejidad adicional que justificar.
