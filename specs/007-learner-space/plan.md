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

Antes de implementar, el contrato base debe publicar en cada inscripción
`module_count`, volver a comprobar que la cuenta esté activa y permitir revertir
`learning:session-current` con `track_id`. Estos son prerequisitos externos y no
amplían los archivos permitidos de esta feature.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, plantillas Django server-rendered y los parciales existentes en `templates/ui/components/`

**Storage**: PostgreSQL 16 en CI autoritativa; la feature es de solo lectura y no añade migraciones

**Testing**: `django.test.TestCase`, Django test runner y Ruff 0.16.3

**Target Platform**: Aplicación web desplegada en Linux/Railway y navegadores modernos con teclado

**Project Type**: Monolito modular Django con interfaz server-rendered

**Performance Goals**: Renderizar listado o estado vacío en menos de 2 segundos bajo condiciones normales, sin consultas por cada track

**Constraints**: Solo lectura; una consulta publicada para las inscripciones; sin métricas calculadas; sin cambios de rutas, settings, modelos, migraciones, servicios ni componentes; conservar protección y redirección existentes

**Scale/Scope**: Una vista, una plantilla canónica, eliminación de una plantilla duplicada y pruebas enfocadas en `tests/ui/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Referencia | Estado previo | Evidencia de diseño |
| --- | --- | --- |
| Principios 1 y 6 | PASS | La spec contiene criterios verificables y el plan define pruebas de listado, vacío, aislamiento y acceso. |
| Principios 2 y 14 | PASS con prerequisito | La vista solo consume `list_enrollments`; `module_count` debe incorporarse a esa proyección publicada antes de implementar. |
| Principios 4, 12 y 13 | PASS con prerequisito | La identidad procede de `request.user`, se conserva `active_account_required` y el servicio base debe volver a comprobar el estado activo. No se presentan identificadores de cuenta. |
| Principios 9 y 11 | PASS | El cambio entrega una pantalla server-rendered y compone los parciales existentes con foco y acciones de teclado. |
| Principio 16 | PASS | El alcance de código queda cerrado a las rutas declaradas en Project Structure y no incluye migraciones. |

**Gate de inicio de implementación**: no ejecutar `/speckit-implement` hasta que
los tres prerequisitos enumerados en [research.md](research.md) estén disponibles.

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
ui/
├── views.py                              # Modificar solo learner_home
└── templates/ui/learner_home.html        # Eliminar la copia de la app

templates/ui/
└── learner_home.html                     # Crear como plantilla canónica

tests/ui/
└── test_learner_home.py                  # Ampliar contratos de /learn/
```

**Structure Decision**: Mantener la vista en la app `ui`, trasladar la plantilla a
la raíz de plantillas del proyecto y concentrar las pruebas de comportamiento en el
módulo existente. `ui/urls.py`, settings, `templates/base.html`, servicios y todos
los archivos de la feature 004 permanecen cerrados.

## Post-Design Constitution Check

**PASS**. El modelo y el contrato de interfaz no introducen escrituras, consultas
directas a modelos de otros módulos, estado de dominio en el cliente ni archivos
fuera del alcance. Los prerequisitos permanecen como gate explícito anterior a la
implementación; no se simulan dentro de la vista ni de la plantilla.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No aplica: el diseño no acepta desviaciones constitucionales.
