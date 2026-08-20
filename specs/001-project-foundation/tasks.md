# tasks.md — Project Foundation

**Feature**: Project Foundation
**Spec**: `specs/001-project-foundation/spec.md`
**Plan**: `specs/001-project-foundation/plan.md`

## Resumen
Lista de tareas ordenadas y ejecutables para preparar la base técnica mínima (monolito modular Django, PostgreSQL,
Gunicorn, WhiteNoise, health check, GitHub Actions, Railway). Se indica qué tareas pueden ejecutarse en paralelo.

---

## Phase 1 — Setup (inicial)

- [x] T001 [P] Crear README del proyecto con resumen y enlaces importantes (`README.md`)
- [x] T002 [P] Crear estructura de directorios propuesta para el monolito y archivos placeholder (`kronolearn/`, `accounts/`, `catalog/`, `learning/`, `gamification/`, `analytics/`, `ui/`, `tests/`)
- [x] T003 [P] Añadir `.env.example` en la raíz del repositorio con las variables mínimas requeridas, usando únicamente valores ficticios y seguros.
- [x] T004 [P] Crear y mantener `docs/deployment/railway.md` con pasos documentados para desplegar en Railway (variables necesarias, build steps, proceso `web`/Procfile-equivalente). Esta tarea incluye la actualización posterior (consolidación de duplicados de documentación Railway).
- [x] T005 [P] Crear canon del contrato del health check en `specs/001-project-foundation/contracts/health-check.md` (ruta `/healthz`, método GET, cuerpo JSON esperado `{"status": "ok"}`, criterios de éxito). Esta tarea centraliza y sustituye duplicados previos de documentación del health-check.
- [x] T006 [P] Crear `docs/dependencies.md` con la política de dependencias reproducibles mediante `requirements.in` y `requirements.txt` con versiones fijadas. Los hashes quedan registrados como mejora posterior.

## Phase 2 — Foundational (prerrequisitos bloqueantes)

- [x] T007 [ ] [US1] Definir estructura de settings por entorno y documentar cómo se leen variables de entorno (`kronolearn/settings/README.md`)
- [x] T008 [ ] Configurar documento `docs/gunicorn-whitenoise.md` con el comando de arranque esperado y la estrategia de servir estáticos (no incluir código) (`docs/gunicorn-whitenoise.md`)
- [x] T009 [P] Implementar y validar `.github/workflows/ci.yml` en el repositorio (lint, formatting, tests rápidos). Esta tarea incluye: crear el workflow, abrir un PR de prueba que ejecute el workflow y documentar el resultado de validación (exit codes, logs relevantes). (Comprobado: PR #1 ejecutado y workflow finalizó correctamente)
- [x] T010 [ ] Documentar la estrategia mínima de pruebas en `specs/001-project-foundation/tests-strategy.md` (unit tests, pruebas críticas en CI, gate de merge)
- [x] T011 [P] Documentar y validar la configuración esperada para PostgreSQL en Railway y local (`docs/db-railway.md`), más tarea de validación automatizada (por ejemplo, `tests/db/test_db_connection.py`) para comprobar `DATABASE_URL` y conexión básica.
- [x] T012 [P] Crear dependencias reproducibles: `requirements.in` y `requirements.txt` contienen versiones fijadas; los hashes quedan como mejora posterior. Esta tarea incluye instrucción de instalación en `docs/dependencies.md`.

## Phase 3 — User Story Phases (por prioridad)

### User Story 1 (P1) — Inicializar infraestructura mínima
Objetivo: Validar despliegue y controles de integración.

- [x] T013 [P] [US1] Implementar prueba ejecutable de health check en `tests/smoke/test_health_check.py` que realice una solicitud GET a `/healthz` y verifique: HTTP 200 y cuerpo JSON `{"status": "ok"}`. Integrar esta prueba en el workflow CI definido en `.github/workflows/ci.yml`.
- [ ] T014 [ ] [US1] Documentar contract de startup y comandos esperados en `specs/001-project-foundation/quickstart.md` (incluir pasos mínimos para arrancar y validar en local y en Railway).
- [ ] T015 [P] [US1] Crear `docs/ci/ci-usage.md` con instrucciones para ejecutar localmente las comprobaciones de CI (lint, format, tests rápidos) y pasos para reproducir fallos de CI.
- [ ] T016 [ ] [US1] Definir los criterios de aceptación automatizables para FR-001..FR-007 y listarlos en `specs/001-project-foundation/acceptance-criteria.md`

## Final Phase — Polish & Cross-Cutting Concerns

- [x] T017 [P] Validar y documentar el despliegue en Railway: ejecutar un despliegue de prueba (o checklist de verificación) y confirmar que el endpoint `/healthz` responde correctamente en el entorno Railway. Registrar pasos y resultados en `docs/deployment/railway.md`.
- [ ] T018 [P] Crear `docs/maintainers.md` con contactos y responsables para despliegue y revisiones de la línea base
- [ ] T019 [ ] Revisar y validar que `specs/001-project-foundation/checklists/requirements.md` está completa y marcar resultados

## Cross-cutting — Frontend preparation

- [ ] T020 [P] Preparar `ui/` para integración frontend mínima: crear carpeta `ui/frontend/` con `package.json` placeholder y documentación en `ui/frontend/README.md` describiendo cómo integrar HTMX, Alpine.js y Tailwind CSS en el monolito.
- [ ] T021 [P] Preparar integración HTMX: documentar uso sugerido y añadir ejemplos en `ui/frontend/htmx-readme.md` (rutas concretas para incluir atributos `hx-*` en templates: `ui/templates/`).
- [ ] T022 [P] Preparar integración Alpine.js: documentar el patrón de inclusión y ejemplos en `ui/frontend/alpine-readme.md` (incluir ubicación recomendada `ui/static/js/`).
- [ ] T023 [P] Preparar integración Tailwind CSS: añadir `ui/frontend/tailwind.md` con instrucciones concretas para configuración (`tailwind.config.js`, `postcss.config.js`) y ejemplo de pipeline de build (scripts npm) para compilar CSS estático servido por WhiteNoise.

## Cross-cutting — DB & Dependencies

- [ ] T024 [P] Validar la configuración de PostgreSQL local y en Railway: crear `tests/db/test_db_connection.py` (smoke test) que use `DATABASE_URL` y haga una conexión simple (success/fail) y documentar cómo ejecutar la prueba.
- [ ] T025 [P] Crear un artefacto de dependencias reproducibles en el repo: `requirements.txt` con versiones fijadas y hashes o `poetry.lock` (según la herramienta elegida). Añadir instrucciones de actualización en `docs/dependencies.md`.

## Cross-cutting — Verification & consolidation

- [ ] T026 [P] Consolidar y cerrar duplicados: asegurar que `specs/001-project-foundation/contracts/health-check.md` y `docs/deployment/railway.md` son las fuentes canónicas; eliminar/archivar referencias duplicadas y actualizar `specs/001-project-foundation/tasks.md` para apuntar a los archivos canónicos.

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

- Total tareas: 26
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
