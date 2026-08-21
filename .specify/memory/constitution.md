<!--
Sync Impact Report

- Version change: 1.0.0 -> 1.1.0
- Modified principles: none; all ten project principles retain their meaning
- Modified sections: Gobernanza -> Governance; amendment, constitutional versioning,
  and compliance review rules made explicit
- Added sections: none
- Removed sections: unresolved generic constitution scaffold preceding the project constitution
- Follow-up TODOs: none

-->

# KronoLearn Constitution

## Core Principles

### 1. Desarrollo guiado por especificaciones

Ninguna funcionalidad puede implementarse antes de contar con su especificación, las aclaraciones necesarias,
un plan técnico, la lista de tareas y criterios de aceptación verificables. Los criterios de aceptación DEBEN ser
automáticamente verificables cuando sea posible (tests, validaciones, scripts de revisión).

### 2. Diseño orientado al dominio

Las reglas de puntuación, rachas, progreso, intentos, versionado de contenido y clasificación semanal DEBEN
pertenecer a servicios de dominio claramente definidos. Estas reglas NO pueden implementarse ni duplicarse en
vistas, templates o fragmentos HTMX. La lógica de negocio central DEBE residir en el módulo de dominio correspondiente.

### 3. Contenido administrado como datos

Los tracks, módulos, microlecciones, casos, opciones, fuentes y laboratorios DEBEN poder configurarse y publicarse
sin modificar el código fuente de la aplicación. La publicación y el versionado DEBEN poder realizarse desde
interfaces administrativas o pipelines de datos controlados.

### 4. Seguridad por defecto

La autenticación, autorización, validación de propiedad de los recursos, protección CSRF, validación del lado del
servidor, administración de secretos y protección de datos privados SON obligatorias. El sistema NUNCA debe confiar
en datos de autorización, puntuación, progreso o valoración provenientes del navegador.

### 5. Idempotencia transaccional

Los envíos repetidos de un intento NUNCA deben duplicar puntos competitivos, progreso, intentos puntuables ni eventos
de puntuación. El registro del intento, la actualización del progreso, el cálculo de la racha y la creación del evento
de puntuación DEBEN ejecutarse dentro de una transacción atómica que garantice idempotencia.

### 6. Pruebas de reglas críticas

Son obligatorias las pruebas automatizadas para:

- cálculo de puntos;
- bonificación y ruptura de rachas;
- identificación del primer intento;
- idempotencia;
- actualización del progreso;
- publicación y versionado de contenido;
- permisos de aprendiz y administrador;
- selección de la siguiente sesión;
- ordenamiento y desempate de la liga semanal.

Estas pruebas DEBEN ejecutarse en CI y bloquear merges si fallan.

### 7. Main siempre desplegable

Todo cambio DEBE llegar a `main` mediante Pull Request y solo puede integrarse después de superar correctamente
los controles de integración continua. La rama `main` DEBE permanecer siempre desplegable en Railway. No se permiten
commits directos a `main`.

### 8. Monolito modular

KronoLearn DEBE implementarse como un monolito modular en Django con los siguientes módulos:

- `accounts`;
- `catalog`;
- `learning`;
- `gamification`;
- `analytics`;
- `ui`.

Durante la línea base NO se deben introducir microservicios, Redis, workers, cron, colas de tareas ni un frontend
desplegado por separado.

### 9. Entrega simple e incremental

El equipo DEBE priorizar el flujo funcional completo del aprendiz sobre el pulido visual y las funcionalidades
opcionales. El flujo prioritario es:

inicio de sesión → exploración → inscripción → sesión diaria → decisión → retroalimentación → puntos → progreso.

Si existe un retraso, se DEBE reducir el contenido precargado o el pulido visual antes de eliminar controles de
seguridad, autorización, idempotencia o pruebas de dominio.

### 10. Contenido trazable y versionado

Cada versión publicada de contenido DEBE conservar como mínimo:

- autor;
- fuente;
- número de versión;
- fecha de revisión;
- estado editorial.

Las versiones publicadas DEBEN ser inmutables y los intentos históricos DEBEN conservar la versión exacta presentada
al aprendiz.

## Restricciones tecnológicas

Las siguientes tecnologías son obligatorias y forman parte del contrato técnico del proyecto:

- Django
- PostgreSQL
- HTMX
- Alpine.js
- Tailwind CSS
- Gunicorn
- WhiteNoise
- GitHub Actions
- Railway

Durante la línea base, no se introducirán otras infraestructuras externas salvo las listadas anteriormente.

## Desarrollo y flujo de trabajo

### Revisión y puertas de calidad

- Todos los cambios DEBEN presentarse como Pull Requests y pasar la suite de CI.
- Los PRs que alteren comportamiento público DEBEN incluir una entrada de changelog y la guía de migración cuando
  corresponda.
- Se requiere al menos una aprobación de un mantenedor o revisor designado antes del merge.

### Versionado y releases

- Se usa versionado semántico: MAJOR.MINOR.PATCH.
- Los cambios incompatibles DEBEN provocar un MAJOR bump y acompañarse de guía de migración.
- Cada release DEBE incluir notas y changelog.

## Governance

- Esta constitución prevalece sobre cualquier práctica, guía o artefacto del proyecto que entre en conflicto con ella.
- Toda enmienda DEBE presentarse en un Pull Request dedicado que actualice el Sync Impact Report, explique el motivo
  y el impacto, incluya un plan de migración cuando corresponda y cuente con la aprobación de un mantenedor.
- La versión de la constitución sigue MAJOR.MINOR.PATCH: MAJOR para eliminaciones o redefiniciones incompatibles de
  principios; MINOR para principios, secciones o reglas materialmente ampliadas; PATCH para aclaraciones sin cambio
  semántico.
- Cada revisión de especificaciones, aclaraciones, planes, tareas, implementaciones y Pull Requests DEBE comprobar
  el cumplimiento constitucional. Las desviaciones no críticas DEBEN documentarse y justificarse en un issue o PR
  enlazado antes de aprobarse.
- Las reglas críticas de seguridad, autorización, pruebas e idempotencia NO pueden omitirse ni exceptuarse para
  cumplir una fecha de entrega.
- Toda enmienda DEBE actualizar la versión y `Last Amended`; `Ratified` conserva la fecha de adopción original.

**Version**: 1.1.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-20
