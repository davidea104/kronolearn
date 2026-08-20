# Feature Specification: Project Foundation

**Feature Branch**: `001-project-foundation`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Preparar la base técnica mínima para el primer despliegue — Proyecto Django, monolito modular, PostgreSQL, variables de entorno, Gunicorn, WhiteNoise, endpoint de health check, GitHub Actions con validaciones básicas, preparación para Railway."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inicializar infraestrucutra mínima (Priority: P1)

Como equipo de desarrollo, queremos disponer de una base técnica mínima para desplegar la aplicación
para poder validar el flujo de despliegue y los controles de integración.

**Why this priority**: Permite validar despliegue y detectar problemas de infraestructuras críticas antes
de desarrollar las historias funcionales de aprendiz.

**Independent Test**: Verificar que el proyecto puede ejecutarse localmente con las variables de entorno mínimas,
que existe un endpoint de health check accesible y que la configuración permite ejecutar Gunicorn con
WhiteNoise en modo simulado.

**Acceptance Scenarios**:

1. **Given** un entorno con las variables de entorno mínimas definidas, **When** se arranca la aplicación, **Then**
   el endpoint de health check responde 200 con estado OK.
2. **Given** un pipeline de CI en GitHub Actions, **When** se ejecuta la validación, **Then** la suite básica de comprobaciones
   (lint, tests unitarios mínimos, comprobación de formatting) finaliza sin errores.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El repositorio DEBE contener la estructura inicial de un proyecto Django preparado como monolito modular.
- **FR-002**: El proyecto DEBE estar preparado para usar PostgreSQL como base de datos en producción.
- **FR-003**: DEBEN definirse las variables de entorno necesarias para configurar la conexión a base de datos,
  settings sensibles y credenciales de despliegue.
- **FR-004**: DEBE existir un endpoint de health check que devuelva un estado operativo básico.
- **FR-005**: DEBE existir configuración para ejecutar la aplicación con Gunicorn y servir archivos estáticos
  con WhiteNoise en producción.
- **FR-006**: DEBE existir un pipeline de GitHub Actions que ejecute comprobaciones básicas (lint, formateo, ejecución
  de tests unitarios rápidos) y falle si alguna comprobación no pasa.
- **FR-007**: La preparación para desplegar en Railway DEBE documentarse (variables necesarias, pasos de build/procfile
  o configuración equivalente) en la especificación.

### Acceptance Criteria por requisito

- **AC-FR-001**: Existe en el repositorio una descripción y estructura de directorios esperada para el monolito modular
  (lista de módulos y ubicación) y un README con instrucciones mínimas para arrancar en modo desarrollo.
- **AC-FR-002**: La especificación incluye la lista de variables y un ejemplo de configuración que permite conectar
  a una instancia PostgreSQL (sin incluir credenciales reales). La preparación documenta cómo validar la conexión.
- **AC-FR-003**: La especificación contiene un listado mínimo de variables de entorno requeridas (por ejemplo: SECRET_KEY,
  DATABASE_URL, RAILWAY_ENVIRONMENT_VARIABLES...) y un ejemplo `env.example` documentado.
- **AC-FR-004**: El contract del health check está definido: ruta (por ejemplo `/healthz`), método (GET) y cuerpo JSON esperado
  (`{"status": "ok"}`) y un criterio de aceptación que define respuesta 200 cuando los checks básicos pasan.
- **AC-FR-005**: La especificación documenta el comando de arranque esperado para producción (Gunicorn) y la estrategia
  de servir estáticos con WhiteNoise (configuración esperada) sin incluir código.
- **AC-FR-006**: El workflow de GitHub Actions documentado lista las comprobaciones que debe ejecutar (lint, formatting, tests
  unitarios rápidos) y un criterio que define cuándo el pipeline falla (exit code != 0).
- **AC-FR-007**: La documentación de despliegue para Railway contiene las variables de entorno mínimas, los pasos de build
  y la instrucción para configurar el proceso de tipo `web` (o Procfile-equivalente) para ejecutar Gunicorn.

### Non-Functional / Technical Preparation (constraints)

- La solución prevista DEBE ser compatible con:
  - Django
  - PostgreSQL
  - Gunicorn
  - WhiteNoise
  - Railway
  - GitHub Actions
  - HTMX, Alpine.js y Tailwind CSS (preparación del frontend en el monolito)

- No se implementarán microservicios, Redis, workers, cron ni colas de tareas en esta fase inicial.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El endpoint de health check responde 200 en menos de 500ms en un entorno local controlado.
- **SC-002**: El pipeline de GitHub Actions completa lint + formateo + tests unitarios rápidos en menos de 10 minutos
  para la rama de especificación.
- **SC-003**: La documentación de despliegue contiene las variables de entorno mínimas y pasos para desplegar en Railway.

## Assumptions

- Se asume que el equipo dispone de una cuenta y acceso a Railway y a un repositorio en GitHub con privilegios
  para configurar GitHub Actions.
- Se asume que la selección concreta de versiones de Django/PostgreSQL se decidirá en la etapa de implementación.
- Mobile y escalado horizontal están fuera del alcance de esta especificación inicial.

## Key Entities

- **Proyecto**: repositorio con la estructura del monolito Django.
- **Entorno de despliegue**: Railway con variables de entorno y configuración de Gunicorn.
- **CI pipeline**: GitHub Actions workflow que ejecuta verificaciones básicas.

## Tasks (informative, no implementar código)

- Crear estructura inicial del proyecto Django (módulos: accounts, catalog, learning, gamification, analytics, ui).
- Documentar variables de entorno necesarias y ejemplo de `.env.example`.
- Definir endpoint de health check y su contract (ruta, método, respuesta JSON mínima).
- Diseñar workflow básico de GitHub Actions (lint, formatting, tests rápidos).
- Documentar pasos para despliegue en Railway (build steps, env vars, proceso de release).

## Dependencies

- Acceso a Railway y permisos para crear el primer deployment.
- Acceso a GitHub Actions para configurar workflows.

## Open Questions ([NEEDS CLARIFICATION] - limit 3)

- Ninguna pregunta crítica necesaria para esta especificación inicial.

## Edge Cases

- Variables de entorno faltantes o malformadas: la documentación debe indicar el comportamiento esperado y cómo detectarlo en CI.
- Base de datos no disponible: el health check debe reflejar degradación y la documentación indicar pasos de recuperación.
- Pipeline de CI intermitente: la spec debe indicar tolerancia y cómo reproducir localmente fallos de CI.
- Conflictos de versiones de dependencias: la documentación debe recomendar fijar versiones mínimas/compatibles durante la línea base.


---

*Spec creada por speckit-specify en español. Listo para `/speckit-plan`.*
