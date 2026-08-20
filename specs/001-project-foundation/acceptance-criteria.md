# Acceptance Criteria — Project Foundation

Fecha: 2026-08-20
Versión: 1.0
Autor: Equipo KronoLearn

Este documento reúne los criterios de aceptación verificables para los requisitos funcionales FR-001..FR-007
definidos en `specs/001-project-foundation/spec.md`, tomando como fuente adicional los contratos y tareas del
proyecto.

Fuentes (canónicas):

- `specs/001-project-foundation/spec.md`
- `specs/001-project-foundation/contracts/health-check.md` (contrato canonical de `/healthz`)
- `docs/deployment/railway.md` (guía canonical de despliegue y validación en Railway)
- `specs/001-project-foundation/tasks.md`

---

## FR-001 — Estructura del monolito modular

Texto del requisito:

El repositorio DEBE contener la estructura inicial de un proyecto Django preparado como monolito modular.

AC-FR-001 (Criterio de aceptación):

Existe en el repositorio una descripción y estructura de directorios esperada para el monolito modular (lista de
módulos y ubicación) y un README con instrucciones mínimas para arrancar en modo desarrollo.

Método de validación:

- Comprobar la presencia de los directorios y archivos descritos.
- Revisar `README.md` y `specs/001-project-foundation/quickstart.md` para instrucciones mínimas.

Comandos verificables:

```bash
ls kronolearn
grep -n "runserver" README.md specs/001-project-foundation/quickstart.md || true
```

Evidencia existente (rutas relativas):

- `kronolearn/` (paquete del proyecto)
- `kronolearn/accounts/__init__.py`
- `kronolearn/catalog/__init__.py`
- `kronolearn/learning/__init__.py`
- `kronolearn/gamification/__init__.py`
- `kronolearn/analytics/__init__.py`
- `kronolearn/ui/__init__.py`
- `README.md`
- `specs/001-project-foundation/quickstart.md`

Estado actual: Cumplido

Justificación: La estructura modular y el README/quickstart existen en las rutas indicadas y contienen instrucciones
mínimas para arrancar en modo desarrollo.

---

## FR-002 — Preparación para PostgreSQL

Texto del requisito:

El proyecto DEBE estar preparado para usar PostgreSQL como base de datos en producción.

AC-FR-002 (Criterio de aceptación):

La especificación incluye la lista de variables y un ejemplo de configuración que permite conectar a una instancia
PostgreSQL (sin incluir credenciales reales). La preparación documenta cómo validar la conexión.

Método de validación:

- Revisar settings para soporte de DATABASE_URL.
- Ejecutar la prueba `tests/db/test_db_connection.py` con `DATABASE_URL` apuntando a una instancia local de PostgreSQL.
- Verificar la documentación de Railway que referencia la base gestionada y la URL pública del health check.

Comandos verificables:

```bash
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

Evidencia existente (rutas relativas):

- `kronolearn/settings/base.py`
- `tests/db/test_db_connection.py`
- `docs/db-railway.md`
- PostgreSQL administrado por Railway (servicio configurado en Railway)
- `/healthz` público validado en: `https://kronolearn-production.up.railway.app/healthz`

Estado actual: Cumplido

Justificación: Settings incluyen parsing y uso de `DATABASE_URL` (`kronolearn/settings/base.py`), existe una prueba
automatizada de conectividad (`tests/db/test_db_connection.py`), y `docs/db-railway.md` documenta el uso en Railway. El
health check público está disponible y Railway provee la base gestionada como se documenta en `docs/deployment/railway.md`.

---

## FR-003 — Variables de entorno

Texto del requisito:

DEBEN definirse las variables de entorno necesarias para configurar la conexión a base de datos, settings sensibles
y credenciales de despliegue.

AC-FR-003 (Criterio de aceptación):

La especificación contiene un listado mínimo de variables de entorno requeridas (por ejemplo: SECRET_KEY,
DATABASE_URL, RAILWAY_ENVIRONMENT_VARIABLES...) y un ejemplo `.env.example` documentado.

Método de validación:

- Revisar la presencia de `.env.example` en la raíz y la documentación en `docs/dependencies.md`/`specs`.
- Comprobar que los settings leen variables de entorno (ver `kronolearn/settings/base.py`).

Comandos verificables:

```bash
ls -la .env.example
grep -n "DATABASE_URL" kronolearn/settings/base.py || true
```

Evidencia existente (rutas relativas):

- `.env.example`
- `kronolearn/settings/base.py`

Estado actual: Cumplido

Justificación: `.env.example` existe en la raíz y `kronolearn/settings/base.py` implementa la lectura y parsing de
`DATABASE_URL` y otras variables obligatorias.

---

## FR-004 — Endpoint de health check

Texto del requisito:

DEBE existir un endpoint de health check que devuelva un estado operativo básico.

AC-FR-004 (Criterio de aceptación):

El contract del health check está definido: ruta `/healthz`, método GET y cuerpo JSON esperado `{"status": "ok"}`.

Método de validación:

- Revisar el contrato en `specs/001-project-foundation/contracts/health-check.md`.
- Ejecutar pruebas smoke (`tests/smoke/test_health_check.py`).
- Verificar el endpoint público en Railway y comprobar respuesta JSON.

Comandos verificables:

```bash
.venv/bin/python -m unittest tests.smoke.test_health_check -v
curl -i http://127.0.0.1:8000/healthz
curl -i https://kronolearn-production.up.railway.app/healthz
```

Evidencia existente (rutas relativas / URLs):

- `specs/001-project-foundation/contracts/health-check.md`
- `kronolearn/health.py`
- `tests/smoke/test_health_check.py`
- `https://kronolearn-production.up.railway.app/healthz` (public)
- Resultado verificado: HTTP 200 y body `{ "status": "ok" }`

Estado actual: Cumplido

Justificación: El contrato existe, la implementación en `kronolearn/health.py` corresponde al contrato, las pruebas
smoke están presentes y la URL pública responde 200 con el body esperado.

---

## FR-005 — Gunicorn y WhiteNoise en producción

Texto del requisito:

DEBE existir configuración para ejecutar la aplicación con Gunicorn y servir archivos estáticos con WhiteNoise en
producción.

AC-FR-005 (Criterio de aceptación):

La especificación documenta el comando de arranque esperado para producción (Gunicorn) y la estrategia de servir
estáticos con WhiteNoise.

Método de validación:

- Revisar `kronolearn/wsgi.py` y `kronolearn/settings/production.py` (si existe) y la documentación `docs/gunicorn-whitenoise.md`.
- Verificar que Railway tiene Build/Start commands y que `collectstatic` se ejecuta en build.

Comandos verificables:

```bash
grep -n "get_wsgi_application" kronolearn/wsgi.py || true
# Verificar collectstatic en el proceso de build de Railway (registro en docs/deployment/railway.md)
```


Evidencia existente (rutas relativas / ejecución en Railway):

- `kronolearn/settings/production.py`
- `kronolearn/wsgi.py`
- `docs/gunicorn-whitenoise.md`
- Build/Start/collectstatic configurados y documentados en Railway (`docs/deployment/railway.md`)
- Build Command ejecutado correctamente: `python manage.py collectstatic --noinput`
- Resultado: 127 archivos estáticos copiados a `/app/staticfiles`
- Resultado: 381 archivos postprocesados
- Gunicorn activo en Railway
- `/healthz` público responde HTTP 200

Estado actual: Cumplido

Justificación: `kronolearn/wsgi.py` y `docs/gunicorn-whitenoise.md` existen y describen el comando de arranque. Los
registros de despliegue en Railway muestran que `collectstatic` se ejecutó correctamente (`python manage.py collectstatic --noinput`),
los artefactos estáticos fueron copiados y postprocesados (127 archivos copiados, 381 postprocesados), Gunicorn está activo
en el entorno de Railway y el endpoint `/healthz` público responde con HTTP 200. Por tanto la verificación end-to-end en
Railway está satisfecha.

---

## FR-006 — Pipeline de GitHub Actions

Texto del requisito:

DEBE existir un pipeline de GitHub Actions que ejecute comprobaciones básicas (lint, formateo, ejecución de tests
unitarios rápidos) y falle si alguna comprobación no pasa.

AC-FR-006 (Criterio de aceptación):

El workflow de GitHub Actions documentado lista las comprobaciones que debe ejecutar (ruff, formatting, tests unitarios
rápidos) y un criterio que define cuándo el pipeline falla (exit code != 0).

Método de validación:

- Revisar `.github/workflows/ci.yml` y la documentación `docs/ci/ci-usage.md`.
- Verificar ejecución exitosa en PR #1 (CI en verde).

Comandos verificables:

```bash
ls -la .github/workflows/ci.yml
# Revisar logs en GitHub Actions UI para PR #1
```

Evidencia existente (rutas relativas / referencias):

- `.github/workflows/ci.yml`
- `docs/ci/ci-usage.md`
- PR #1 con CI en verde (registro de ejecución en GitHub Actions)

Estado actual: Cumplido

Justificación: El workflow existe en `.github/workflows/ci.yml`, la guía `docs/ci/ci-usage.md` documenta su uso y PR #1
se registró con ejecución exitosa del pipeline.

---

## FR-007 — Documentación de despliegue en Railway

Texto del requisito:

La preparación para desplegar en Railway DEBE documentarse (variables necesarias, pasos de build/procfile o configuración
equivalente) en la especificación.

AC-FR-007 (Criterio de aceptación):

La documentación de despliegue para Railway contiene las variables de entorno mínimas, los pasos de build y la instrucción
para configurar el proceso de tipo `web` (o Procfile-equivalente) para ejecutar Gunicorn.

Método de validación:

- Revisar `docs/deployment/railway.md` y `specs/001-project-foundation/quickstart.md`.
- Verificar que el despliegue en Railway está activo y responde al health check público.

Comandos verificables:

```bash
grep -n "collectstatic" docs/deployment/railway.md || true
curl -i https://kronolearn-production.up.railway.app/healthz
```

Evidencia existente (rutas relativas / URLs):

- `docs/deployment/railway.md`
- `specs/001-project-foundation/quickstart.md`
- Despliegue activo en Railway: `kronolearn-production.up.railway.app`

Estado actual: Cumplido

Justificación: La documentación de despliegue existe (`docs/deployment/railway.md` y `specs/001-project-foundation/quickstart.md`) y
el despliegue público responde correctamente al endpoint `/healthz`.

---

## Matriz de trazabilidad

Requisito | Criterio de aceptación | Evidencia | Estado
---|---|---|---
FR-001 | AC-FR-001 | `kronolearn/`, `README.md`, `specs/001-project-foundation/quickstart.md` | Cumplido
FR-002 | AC-FR-002 | `kronolearn/settings/base.py`, `tests/db/test_db_connection.py`, `docs/db-railway.md`, PostgreSQL (Railway), `https://kronolearn-production.up.railway.app/healthz` | Cumplido
FR-003 | AC-FR-003 | `.env.example`, `kronolearn/settings/base.py` | Cumplido
FR-004 | AC-FR-004 | `specs/001-project-foundation/contracts/health-check.md`, `kronolearn/health.py`, `tests/smoke/test_health_check.py`, `https://kronolearn-production.up.railway.app/healthz` | Cumplido
FR-005 | AC-FR-005 | `kronolearn/settings/production.py`, `kronolearn/wsgi.py`, `docs/gunicorn-whitenoise.md`, `docs/deployment/railway.md` (Build/Start/collectstatic), Build: `python manage.py collectstatic --noinput` (127 files copied, 381 postprocessed), Gunicorn active, `/healthz` -> HTTP 200 | Cumplido
FR-006 | AC-FR-006 | `.github/workflows/ci.yml`, `docs/ci/ci-usage.md`, PR #1 (CI verde) | Cumplido
FR-007 | AC-FR-007 | `docs/deployment/railway.md`, `specs/001-project-foundation/quickstart.md`, `https://kronolearn-production.up.railway.app` | Cumplido

---

## Notas finales

- Este documento cubre exclusivamente los criterios de aceptación para la fase Project Foundation.
- No incluye pasos pendientes de futuras historias de usuario relacionadas con reglas de negocio, scoring o domain logic.
- Los estados se han determinado a partir de la evidencia encontrada en el repositorio y verificaciones documentales al
  2026-08-20.
