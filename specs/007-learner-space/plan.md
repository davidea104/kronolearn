# Implementation Plan: Espacio de aprendizaje

**Branch**: `007-learner-space` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-learner-space/spec.md`

## Summary

Reemplazar el contenido de `/learn/` por una proyección server-rendered de las
inscripciones de la cuenta activa. `learner_home` conserva su decorador, invoca una
sola vez `learning.services.enrollment.list_enrollments(request.user)` y entrega el
resultado a una plantilla única bajo `templates/ui/`. La plantilla compone cada
entrada con los parciales existentes de tarjeta y botón, y usa el parcial de estado
vacío cuando no hay resultados.

Como tarea fundacional, esta feature completa el contrato base para publicar
`module_count`, volver a comprobar que la cuenta esté activa y permitir revertir
`learning:session-current` con `track_id`. La ruta temporal responde `200` sin
seleccionar contenido; la spec 009 reemplazará su cuerpo conservando el contrato.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, plantillas Django server-rendered y los parciales existentes en `templates/ui/components/`

**Storage**: PostgreSQL 16 en CI autoritativa; la feature es de solo lectura y no añade migraciones

**Testing**: `django.test.TestCase`, Django test runner y Ruff 0.16.3

**Target Platform**: Aplicación web desplegada en Linux/Railway y navegadores modernos con teclado

**Project Type**: Monolito modular Django con interfaz server-rendered

**Performance Goals**: Renderizar listado o estado vacío en menos de 2 segundos bajo condiciones normales, sin consultas por cada track

**Constraints**: Solo lectura; una consulta publicada para las inscripciones; sin métricas calculadas; sin cambios de settings, modelos, migraciones ni componentes; no implementar `enroll()` ni selección de sesión

**Scale/Scope**: Una vista, una plantilla canónica, eliminación de una plantilla duplicada y pruebas enfocadas en `tests/ui/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Referencia | Estado previo | Evidencia de diseño |
| --- | --- | --- |
| Principios 1 y 6 | PASS | La spec contiene criterios verificables y el plan define pruebas de listado, vacío, aislamiento y acceso. |
| Principios 2 y 14 | PASS | La vista solo consume `list_enrollments`; la tarea fundacional incorpora `module_count` a esa proyección publicada. |
| Principios 4, 12 y 13 | PASS | La identidad procede de `request.user`, se conserva `active_account_required` y el servicio vuelve a comprobar el estado persistido. No se presentan identificadores de cuenta. |
| Principios 9 y 11 | PASS | El cambio entrega una pantalla server-rendered y compone los parciales existentes con foco y acciones de teclado. |
| Principio 16 | PASS | El alcance de código queda cerrado a las rutas declaradas en Project Structure y no incluye migraciones. |

**Gate de historias**: completar y verificar la tarea fundacional T002 antes de
iniciar las tareas asociadas a historias de usuario.

## Project Structure

### Documentation (this feature)

```text
specs/007-learner-space/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── learner-home.md  # Contrato HTML y de contexto de /learn/
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
learning/
├── services/enrollment.py                # Revalidar cuenta y anotar module_count
├── urls/session.py                       # Publicar session-current(track_id)
└── views/session/
    └── current.py                        # Placeholder protegido

templates/learning/session/
└── current.html                          # Documento temporal accesible

ui/
├── views.py                              # Modificar solo learner_home
└── templates/ui/learner_home.html        # Eliminar la copia de la app

templates/ui/
├── learner_home.html                     # Crear como plantilla canónica
└── components/card.html                  # Añadir API estructurada y segura

tests/ui/
└── test_learner_home.py                  # Ampliar contratos de /learn/

tests/learning/
├── test_enrollment_contracts.py          # Revalidación, conteo y consultas
└── session/
    └── test_current_placeholder.py       # Ruta y placeholder temporal

tests/integration/test_root_contracts.py   # Actualizar expectativa de ruta hoja
docs/contracts/domain-contracts.md         # Publicar excepción al baseline
CHANGELOG.md                               # Registrar comportamiento público
```

**Structure Decision**: Mantener la vista en la app `ui`, trasladar la plantilla a
la raíz de plantillas del proyecto, ampliar de forma compatible `card.html` para no
pasar títulos administrables por `content|safe` y completar los contratos faltantes
en los paths hoja ya reservados por la 004. `ui/urls.py`,
`learning/urls/__init__.py`, settings, modelos, migraciones, `templates/base.html`,
`enroll()` y los servicios reales de sesión permanecen cerrados.

## Post-Design Constitution Check

**PASS**. El modelo y el contrato de interfaz no introducen escrituras, consultas
directas desde presentación, estado de dominio en el cliente ni archivos fuera del
alcance. La autorización se revalida en el servicio y el placeholder no selecciona
ni revela contenido de sesión.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No aplica: el diseño no acepta desviaciones constitucionales.
