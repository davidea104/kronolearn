# Implementation Plan: Project Foundation

**Branch**: `001-project-foundation` | **Date**: 2026-08-19 | **Spec**: `specs/001-project-foundation/spec.md`

**Input**: Feature specification from `specs/001-project-foundation/spec.md`

## Summary

Plan técnico para preparar la base mínima de KronoLearn compatible con la constitución del proyecto. Se
establece una arquitectura de monolito modular en Django, preparación para PostgreSQL mediante variables de
entorno, configuración de Gunicorn y WhiteNoise para producción, un endpoint de health check, workflows básicos
de GitHub Actions y documentación para despliegue en Railway. La estrategia mínima de pruebas cubre unit tests
y pruebas de reglas críticas en el pipeline.

## Technical Context

**Language/Version**: Python 3.14 (línea base para la implementación)

**Primary Dependencies**: Django 5.2 LTS (usar la versión patch más reciente compatible), Gunicorn, WhiteNoise,
psycopg (psycopg 3) con soporte binario para desarrollo (`psycopg[binary]`).

**Storage**: PostgreSQL (conexión vía `DATABASE_URL` o variable equivalente definida en variables de entorno)

**Testing**: Unit tests con un runner de Python (por ejemplo `pytest` o `django test`) para la línea base; integración
de tests críticos en CI. (Runner exacto a definir en implementación.)

**Target Platform**: Linux server (Railway deployment target)

**Project Type**: Web application monolith (Django)

**Performance Goals**: No objetivos de rendimiento elevados en la línea base; el foco es estabilidad y despliegue fiable.

**Constraints**: Mantener compatibilidad con la constitución: test-first para reglas críticas, idempotencia transaccional
en flujos de scoring, seguridad por defecto (no confiar en datos del navegador), main siempre desplegable.

**Scale/Scope**: Línea base enfocada en validar despliegue y pruebas; escalado horizontal e infraestructuras externas
quedan fuera de alcance.

**Dependencias reproducibles**: Todas las dependencias DEBEN fijarse mediante un archivo de dependencias reproducible
(por ejemplo `requirements.txt` con hashes o `poetry.lock`). Esto asegura builds reproducibles y cumplimiento con la
política de versiones.

## Constitution Check

Gates extraídos de la constitución que aplican a este plan:

- Desarrollo guiado por especificaciones: la spec existe y este plan deriva de ella — PASS
- Diseño orientado al dominio: las reglas de negocio deben residir en módulos de dominio — ENFORCED (ver Data Model)
- Contenido administrado como datos: el plan incluye preparación para gestión de contenido como datos — PASS
- Seguridad por defecto: el plan exige validaciones y no confiar en datos del navegador — PASS
- Idempotencia transaccional: se exige en la estrategia de pruebas y diseño de transacciones — PASS
- Pruebas de reglas críticas: plan incluye exigencia de tests en CI para reglas críticas — PASS
- Main siempre desplegable: workflows de CI y checks definidos para mantener `main` desplegable — PASS
- Monolito modular: plan define los módulos obligatorios y prohíbe microservicios en línea base — PASS
- Entrega simple e incremental: plan prioriza flujo del aprendiz y despliegue — PASS
- Contenido trazable y versionado: plan exige documentación y versionado de contenido — PASS

Resultado de la comprobación constitucional: No se detectan violaciones a la constitución en este plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-project-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md  # NOT created by /speckit-plan
```

### Source Code (propuesta de estructura en monolito Django)

```text
kronolearn/
├── manage.py
├── kronolearn/                # project settings
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── accounts/                  # módulos de aplicación
├── catalog/
├── learning/
├── gamification/
├── analytics/
└── ui/

tests/
├── unit/
├── integration/
└── smoke/
```

**Structure Decision**: Se adopta el monolito modular en Django con apps por dominio tal como exige la constitución.

## Complexity Tracking

No se identifican violaciones de la constitución que requieran excepciones justificadas en este plan.

