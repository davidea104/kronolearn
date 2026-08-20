# Maintainers and Responsibilities — Project Foundation

Fecha: 2026-08-20
Versión: 1.0

Propósito
---------

Documento de referencia para roles, responsabilidades y procedimientos de coordinación relacionados con la
línea base del proyecto (Project Foundation). Cubre quiénes (roles) deben intervenir en despliegues, revisiones
y handoffs, y qué archivos requieren coordinación especial.

Alcance
-------

Este documento aplica únicamente a la fase Project Foundation y a los artefactos dentro de
`specs/001-project-foundation/` y la infraestructura mínima documentada en el repositorio. No incluye normas
operativas fuera del repositorio ni secretos.

Roles (placeholders)
--------------------

- ROLE_TECH_LEAD — Responsable técnico
- ROLE_CONTENT_LEAD — Responsable de contenido
- ROLE_RAILWAY_ADMIN — Responsable de Railway / despliegue
- ROLE_CI_OWNER — Responsable de CI y GitHub Actions
- ROLE_SECURITY_OWNER — Responsable de seguridad
- ROLE_PR_REVIEW_OWNER — Responsable de revisión de Pull Requests

Responsabilidades (resumen por rol)
----------------------------------

- ROLE_TECH_LEAD: decide cambios técnicos de alto impacto, aprueba arquitectura, coordina incidentes técnicos.
- ROLE_CONTENT_LEAD: responsable de la validez editorial de specs, quickstarts y contenidos de aprendizaje.
- ROLE_RAILWAY_ADMIN: gestiona despliegues en Railway, configura variables de entorno en la plataforma y valida
  despliegues iniciales.
- ROLE_CI_OWNER: mantiene `.github/workflows/ci.yml`, define gates de CI y revisa fallos recurrentes en pipelines.
- ROLE_SECURITY_OWNER: evalúa y prioriza vulnerabilidades, define medidas de mitigación y revisiones de seguridad.
- ROLE_PR_REVIEW_OWNER: coordina revisiones de Pull Requests y verifica checklist de PR antes del merge.

Procedimiento de escalamiento ante fallos
----------------------------------------

1. Detectar y registrar el incidente como Issue en el repositorio con la etiqueta `incident` o `sev-*`.
2. Notificar a ROLE_TECH_LEAD y ROLE_RAILWAY_ADMIN (mediante el canal de comunicación del equipo).
3. Realizar triage inmediato: definir impacto y mitigación temporal (rollback, mantenimiento en modo read-only,
   o activar página de mantenimiento).
4. Si el incidente afecta producción o datos, ROLE_SECURITY_OWNER participa en el análisis y mitigación.
5. Documentar la resolución y crear un post-mortem enlazado al Issue con pasos de follow-up y responsable asignado.

Procedimiento de handoff (ejemplo)
---------------------------------

Ejemplo de handoff mínimo cuando se transfiere responsabilidad operativa de una tarea/feature:

- Artefactos a incluir: link a PR/branch, resumen del cambio, comandos de despliegue, pointers a tests críticos,
  y checklist de verificación.
- Confirmaciones necesarias: ROLE_TECH_LEAD y ROLE_RAILWAY_ADMIN deben indicar aceptación del handoff mediante
  comentario en el Issue o PR.

Ejemplo (texto de ejemplo a incluir en el handoff):

```
Handoff: Feature X
- Branch: feature/XYZ
- Resumen: añade endpoint /healthz y workflow CI básico
- Comandos despliegue: python manage.py migrate --noinput; python manage.py collectstatic --noinput; gunicorn kronolearn.wsgi:application
- Tests críticos: tests/smoke/test_health_check.py, tests/db/test_db_connection.py
- Responsable temporal: ROLE_TECH_LEAD
Confirmación de recepción: ROLE_RAILWAY_ADMIN
```

Checklist mínimo antes del merge (por PR)
----------------------------------------

- Descripción del cambio y ticket asociado.
- Tests locales relevantes ejecutados y pasos documentados (`tests/` o comando equivalente).
- Linter/format OK (`ruff check` / `ruff format --check`).
- CI configurado y, si aplica, PR con CI en verde (o evidencia documentada de validación).
- Revisión por ROLE_PR_REVIEW_OWNER (al menos una aprobación para cambios no triviales).
- Persona responsable del despliegue asignada (placeholder role) antes del merge.
- Documentación actualizada si el cambio afecta operativo o quickstart.

Regla: asignar una persona antes de comenzar cada tarea
-----------------------------------------------------

- Cada tarea debe tener una persona/role asignado en el Issue o en la tarjeta de trabajo antes de iniciar.
- Excepción: corrección menor de estilo o typo que no afecte código o documentación operativa (definir en equipo).

Regla: evitar que dos personas modifiquen simultáneamente el mismo archivo
-------------------------------------------------------------------------

- Convención práctica: antes de modificar archivos críticos (lista en este documento), crear un Issue y
  asignar un role; añadir un comentario "working on it". Esto funciona como bloqueo comunicacional ligero.
- Se recomienda ramas por tarea/issue y PR pequeño para reducir conflictos. Para archivos críticos, coordinar con
  ROLE_TECH_LEAD y ROLE_PR_REVIEW_OWNER.

Archivos que requieren coordinación
----------------------------------

Los siguientes archivos y rutas requieren coordinación explícita (Issue + asignación) antes de cambios:

- `specs/001-project-foundation/tasks.md`
- `docs/deployment/railway.md`
- `.github/workflows/ci.yml`
- `kronolearn/settings/` (carpeta y archivos dentro)
- `requirements.in`
- `requirements.txt`

Referencia normativa
--------------------

Este documento se mantiene en conformidad con la constitución del proyecto:
`.specify/memory/constitution.md` (las decisiones y excepciones deben respetar la constitución).

Metadatos
---------

- Fecha: 2026-08-20
- Versión: 1.0
- Última revisión: ROLE_TECH_LEAD (placeholder)