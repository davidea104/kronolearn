# tasks.md — Project Foundation

**Feature**: Project Foundation
**Spec**: `specs/001-project-foundation/spec.md`
**Plan**: `specs/001-project-foundation/plan.md`

## Resumen
Lista de tareas ordenadas y ejecutables para preparar la base técnica mínima (monolito modular Django, PostgreSQL,
Gunicorn, WhiteNoise, health check, GitHub Actions, Railway). Se indica qué tareas pueden ejecutarse en paralelo.

---

## Phase 1 — Setup (inicial)

- [ ] T001 [P] Crear README del proyecto con resumen y enlaces importantes (`README.md`)
- [ ] T002 [P] Crear estructura de directorios propuesta para el monolito y archivos placeholder (`kronolearn/`, `accounts/`, `catalog/`, `learning/`, `gamification/`, `analytics/`, `ui/`, `tests/`)
- [ ] T003 [P] Añadir `specs/001-project-foundation/.env.example` con variables mínimas listadas (SECRET_KEY, DATABASE_URL, RAILWAY_*, etc.)
- [ ] T004 [P] Crear `docs/deployment/railway.md` con pasos documentados para desplegar en Railway (variables necesarias, build steps, proceso `web`/Procfile-equivalente)
- [ ] T005 [P] Crear `specs/001-project-foundation/contracts/health-check.md` con el contrato del health check (ruta, método, cuerpo JSON esperado, criterios de éxito)
- [ ] T006 [P] Crear `docs/dependencies.md` que documente la política de dependencias reproducibles y el archivo previsto (`requirements.txt` o `poetry.lock`)

## Phase 2 — Foundational (prerrequisitos bloqueantes)

- [ ] T007 [ ] [US1] Definir estructura de settings por entorno y documentar cómo se leen variables de entorno (`kronolearn/settings/README.md`)
- [ ] T008 [ ] Configurar documento `docs/gunicorn-whitenoise.md` con el comando de arranque esperado y la estrategia de servir estáticos (no incluir código) (`docs/gunicorn-whitenoise.md`)
- [ ] T009 [ ] Crear borrador de GitHub Actions workflow para CI en ` .github/workflows/ci.yml` (documentar pasos: lint, formatting, tests rápidos)
- [ ] T010 [ ] Documentar la estrategia mínima de pruebas en `specs/001-project-foundation/tests-strategy.md` (unit tests, pruebas críticas en CI, gate de merge)
- [ ] T011 [ ] Documentar la configuración esperada para PostgreSQL en Railway y cómo validar la conexión (`docs/db-railway.md`)

## Phase 3 — User Story Phases (por prioridad)

### User Story 1 (P1) — Inicializar infraestructura mínima
Objetivo: Validar despliegue y controles de integración.

- [ ] T012 [ ] [US1] Documentar contract de startup y commands esperados en `specs/001-project-foundation/quickstart.md` (verificar que incluye steps de validación)
- [ ] T013 [P] [US1] Crear `tests/smoke/test_health_check.py` con especificación de prueba para el endpoint de health check (test vacío/placeholder con descripción de assertions)
- [ ] T014 [ ] [US1] Documentar endpoint de health check y la ubicación sugerida para la implementación (`specs/001-project-foundation/contracts/health-check.md` referencia)
- [ ] T015 [P] [US1] Crear `docs/ci/ci-usage.md` con instrucciones para ejecutar localmente las comprobaciones de CI (lint, format, tests rápidos)
- [ ] T016 [ ] [US1] Definir los criterios de aceptación automatizables para FR-001..FR-007 y listarlos en `specs/001-project-foundation/acceptance-criteria.md`

## Final Phase — Polish & Cross-Cutting Concerns

- [ ] T017 [P] Actualizar `docs/deployment/railway.md` con el ejemplo de variables y notas de seguridad (no incluir secretos)
- [ ] T018 [P] Crear `docs/maintainers.md` con contactos y responsables para despliegue y revisiones de la línea base
- [ ] T019 [ ] Revisar y validar que `specs/001-project-foundation/checklists/requirements.md` está completa y marcar resultados

---

## Dependencias y orden de ejecución

- Phase 1 (T001..T006) puede ejecutarse principalmente en paralelo; T002 (estructura de directorios) es recomendable completarla antes de T007 y T009.
- Phase 2 (T007..T011) bloquea Phase 3; T009 (CI workflow draft) debe existir antes de ejecutar pruebas automáticas (T013).
- Phase 3 (T012..T016) depende de que Phase 2 documente claramente settings, CI y DB (T007..T011).
- Final Phase (T017..T019) puede ejecutarse en paralelo con actividad de Phase 3 para tareas documentales.

## Paralelización (ejemplos)

- Paralelizables simultáneamente: T001, T002, T003, T004, T006, T005 (documentación y creación de directorios)
- Paralelizables durante Phase 3: T013 y T015 pueden ejecutarse en paralelo; T014 y T016 requieren completar T005 y T007 primero.

## Conteo y desglose

- Total tareas: 19
- Tasks por story:
  - US1: T012, T013, T014, T015, T016 (5 tareas)
- Tasks paralelizables marcadas con [P]

## Estrategia de implementación (MVP primero)

1. Ejecutar Phase 1 para disponer de documentación mínima y estructura de proyecto.
2. Completar Phase 2 para definir settings, CI y DB (bloqueantes).
3. Implementar y validar User Story 1 (Phase 3) con pruebas smoke y CI.
4. Completar Final Phase para pulir documentación y responsabilizaciones.

---

*Archivo generado por speckit-tasks basado en spec/plan/research/data-model/quickstart.*
