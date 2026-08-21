# Implementation Plan: Administracion de tracks y modulos

**Branch**: `003-manage-tracks-modules` | **Date**: 2026-08-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-manage-tracks-modules/spec.md`

## Summary

Crear en el modulo `catalog` la administracion transaccional de tracks y modulos, su orden estable, publicacion versionada, auditoria con referencias fallidas no reversibles y consulta segura para aprendices. El diseno usa modelos Django con restricciones de integridad, servicios de dominio atomicos para mutaciones, deteccion optimista de cambios obsoletos antes de evaluar idempotencia, vistas delgadas protegidas por roles y templates server-rendered con respuestas HTMX puntuales.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, psycopg 3.3.4, HTMX, Alpine.js y Tailwind CSS dentro del frontend server-rendered existente

**Storage**: PostgreSQL 16 en CI y produccion; SQLite en memoria para la suite rapida, con pruebas PostgreSQL dedicadas para semantica de bloqueo y concurrencia

**Testing**: `django.test.TestCase` y `TransactionTestCase` mediante `python manage.py test --settings=kronolearn.settings.test`; Ruff 0.16.3 para lint y formato; `python manage.py check` y comprobacion de migraciones

**Target Platform**: Aplicacion web Linux desplegada en Railway con Gunicorn 26.1.0 y WhiteNoise 6.12.0

**Project Type**: Monolito modular Django con templates HTML y mejoras progresivas HTMX/Alpine.js

**Performance Goals**: Percentil 95 menor de 2 segundos en 200 solicitudes validas medidas, distribuidas en 50 creaciones, 50 ediciones, 50 reordenamientos y 50 cambios de estado, despues de excluir 20 solicitudes de calentamiento, con 100 tracks y 50 modulos por track y sin latencia de red publica

**Constraints**: Mutaciones atomicas; autorizacion y validacion en servidor; CSRF obligatorio; versiones publicadas inmutables y nueva version en cada reactivacion real; revision comprobada antes de idempotencia; fuente libre no vacia hasta 500 caracteres; auditoria por solicitud que alcanza el servicio sin persistir referencias fallidas en claro; sin eliminacion fisica; respuestas de acceso a contenido inactivo sin filtraciones; sin servicios, colas o caches externos

**Scale/Scope**: Hasta 100 tracks y 5.000 modulos en el escenario de aceptacion; dos roles consumidores; interfaces administrativas y de consulta del aprendiz; seis modelos persistentes (`CatalogState`, `Track`, `Module`, dos tipos de version y `CatalogChangeLog`). La vinculacion de intentos historicos desde `learning` queda fuera de esta feature; las versiones inmutables constituyen su contrato de integracion futuro

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS - Desarrollo guiado por especificaciones**: `spec.md` esta aclarado, contiene 19 requisitos verificables y precede al diseno tecnico; `/speckit-tasks` producira la descomposicion ejecutable antes de implementar.
- **PASS - Diseno orientado al dominio**: ordenamiento, concurrencia, publicacion, versionado y auditoria residiran en servicios de `catalog`, no en vistas ni templates.
- **PASS - Contenido administrado como datos**: tracks, modulos, estados, posiciones y versiones se persistiran y gestionaran mediante interfaces administrativas sin cambios de codigo.
- **PASS - Seguridad por defecto**: las vistas exigiran sesion activa, comprobaran `CONTENT_ADMIN_ROLE`, validaran CSRF y derivaran actor y autorizacion exclusivamente del servidor.
- **PASS - Idempotencia transaccional**: las mutaciones se ejecutaran dentro de transacciones; restricciones, bloqueos y revision esperada impediran estados parciales y sobrescrituras obsoletas.
- **PASS - Pruebas de reglas criticas**: la suite cubrira permisos, publicacion/versionado, ordenamiento, concurrencia, visibilidad activa, inmutabilidad e historial.
- **PASS - Main desplegable**: el plan conserva los comandos y gates de CI, incluye migraciones y no modifica el proceso de despliegue Railway.
- **PASS - Monolito modular**: toda la capacidad pertenece a la app Django `catalog`; `ui` solo enlaza la experiencia del aprendiz y no se introduce infraestructura externa.
- **PASS - Entrega incremental**: el diseno prioriza administracion basica y catalogo activo; elimina borradores, eliminacion permanente, traslado entre tracks y segmentacion automatica.
- **PASS - Contenido trazable y versionado**: versiones separadas e inmutables conservaran autor, fuente, numero por elemento, fecha de revision y estado editorial; las referencias historicas apuntaran a esas versiones.
- **PASS - Restricciones tecnologicas**: se mantiene Django/PostgreSQL/HTMX/Alpine.js/Tailwind/Gunicorn/WhiteNoise/GitHub Actions/Railway sin dependencias de infraestructura adicionales.

**Gate inicial**: APROBADO. No hay desviaciones constitucionales que requieran Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-manage-tracks-modules/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
catalog/
├── admin.py                       # Consulta protegida de versiones y auditoria
├── forms.py                       # Entradas administrativas y metadatos editoriales
├── models.py                      # Estado de catalogo, tracks, modulos, versiones y auditoria
├── urls.py                        # Contratos web administrativos y del aprendiz
├── views.py                       # Autorizacion, renderizado y adaptacion HTTP
├── migrations/
│   └── 0001_initial.py            # Esquema, indices y restricciones del catalogo
└── services/
    ├── __init__.py
    ├── content.py                 # Crear, editar y cambiar estado con versionado
    ├── ordering.py                # Reordenamientos atomicos y deteccion obsoleta
    └── queries.py                 # Lecturas administrativas y catalogo activo

templates/catalog/
├── learner_track_list.html        # Tracks activos para el aprendiz
├── learner_track_detail.html      # Modulos activos de un track
├── manage_track_list.html         # Lista, estados y controles de orden
├── manage_track_form.html         # Alta y edicion de track
├── manage_module_list.html        # Modulos, estados y controles de orden
├── manage_module_form.html        # Alta y edicion de modulo
└── partials/
    ├── track_rows.html             # Fragmento HTMX de orden/estado de tracks
    └── module_rows.html            # Fragmento HTMX de orden/estado de modulos

ui/templates/ui/
└── learner_home.html              # Enlace hacia el catalogo activo

kronolearn/
└── urls.py                        # Inclusion del namespace catalog

tests/catalog/
├── __init__.py
├── test_models.py                 # Restricciones, identidad e inmutabilidad
├── test_content_services.py       # Creacion, estados, reactivacion, versiones y auditoria
├── test_ordering_services.py      # Orden, atomicidad y conflictos obsoletos
├── test_queries.py                # Visibilidad de tracks/modulos activos
├── test_admin_views.py            # Permisos, CSRF, formularios y respuestas HTMX
└── test_learner_views.py          # Catalogo activo y no divulgacion
```

**Structure Decision**: Extender el monolito existente dentro de `catalog`, siguiendo las fronteras de `accounts`: modelos persistentes, servicios transaccionales y vistas basadas en funciones. Las consultas reutilizables viven en `catalog/services/queries.py`; `ui` conserva solo el punto de entrada visual. Los templates permanecen en el directorio raiz `templates/`, consistente con `TEMPLATES["DIRS"]`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No aplica: el gate inicial y la reevaluacion post-diseno no identifican violaciones.

## Phase 0: Research Decisions

Las decisiones y alternativas se consolidan en [research.md](research.md). No quedan marcadores `NEEDS CLARIFICATION` antes de Phase 1.

## Phase 1: Design Outputs

- [data-model.md](data-model.md): entidades, campos, restricciones, relaciones y transiciones.
- [contracts/web.md](contracts/web.md): rutas HTML/HTMX, autorizacion, entradas, respuestas y errores observables.
- [quickstart.md](quickstart.md): escenarios ejecutables de validacion end-to-end.

## Constitution Check - Post-Design

- **PASS**: El modelo ubica toda regla critica en `catalog`, publica cada transicion real a activo y conserva versiones inmutables con trazabilidad completa. Los intentos futuros de `learning` deberan referenciar la version presentada mediante la relacion protegida definida como contrato diferido.
- **PASS**: Los contratos exigen sesion, rol, CSRF, revision esperada comprobada antes de idempotencia y respuestas sin divulgacion para contenido no visible ni referencias fallidas.
- **PASS**: El diseno usa exclusivamente el monolito y las tecnologias constitucionales; no agrega infraestructura ni dependencias externas.
- **PASS**: El quickstart cubre permisos, ordenamiento, conflictos incluidos no-op obsoletos, reactivacion versionada, auditoria no reversible, invisibilidad del contenido inactivo y el protocolo exacto de rendimiento.

**Gate post-diseno**: APROBADO. La feature puede avanzar a `/speckit-tasks` cuando los artefactos de Phase 0 y Phase 1 esten presentes y validados.
