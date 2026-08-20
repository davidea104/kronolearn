# quickstart.md

Objetivo
--------

Guía rápida para preparar el entorno de desarrollo local y validar el endpoint de health check. Está orientada a
desarrolladores que trabajan en la rama `feature/HU-00-project-foundation`.

Repositorio
----------

Clona el repositorio oficial:

```bash
git clone https://github.com/davidea104/kronolearn.git
cd kronolearn
git checkout feature/HU-00-project-foundation
```

Requisitos previos
------------------

- Git
- Python 3.14 (o compatible con la línea base)
- pip
- PostgreSQL 16 (instalado localmente para desarrollo)
- Gunicorn (opcional, para pruebas locales en modo producción)

NOTA: No se requiere Node.js / npm en esta fase; la preparación frontend todavía no está implementada.

Entorno virtual
---------------

Crear y activar el entorno virtual (macOS / zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
# O usar .venv/bin/python directamente en comandos si no se activa el entorno
```

Instalación de dependencias
---------------------------

Instala desde `requirements.txt`:

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Crear `.env` desde `.env.example`
--------------------------------

Copiar el ejemplo y cargar variables de entorno de forma segura:

```bash
cp .env.example .env
set -a
source .env
set +a
```

No incluyas el fichero `.env` en el control de versiones. No utilizar métodos basados en `grep | xargs` para exportar variables aquí.

Configuración de PostgreSQL local
-------------------------------

Configura una base de datos y un usuario localmente. Por ejemplo (abstracto):

```bash
createuser --pwprompt kronolearn
createdb --owner=kronolearn kronolearn_db
```

La contraseña solicitada al crear el usuario es local y no debe documentarse en el repositorio; debe coincidir con la cadena `DATABASE_URL` en `.env`.

Actualiza `DATABASE_URL` en `.env` para apuntar a tu instancia local (usar placeholders, no valores reales en el repo).

Cargar variables y ejecutar migraciones
--------------------------------------

Tras cargar `.env` (ver más arriba), ejecuta las migraciones:

```bash
.venv/bin/python manage.py migrate
```

Desarrollo local con runserver
------------------------------

Arrancar la app en modo desarrollo (usa la configuración `development`):

```bash
export DJANGO_SETTINGS_MODULE=kronolearn.settings.development
export DEBUG=True
.venv/bin/python manage.py runserver
```

Puesta en marcha local con Gunicorn (modo producción simulado)
-----------------------------------------------------------

Para pruebas locales con Gunicorn debes usar la configuración de producción y variables seguras. Ejemplo:

```bash
export DJANGO_SETTINGS_MODULE=kronolearn.settings.production
export DEBUG=False
export ALLOWED_HOSTS=localhost,127.0.0.1
export SECURE_SSL_REDIRECT=False
export PORT=8000
.venv/bin/gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT
```

Validación del endpoint /healthz (local)
---------------------------------------

Comprueba que el endpoint responde correctamente (usar curl -i para ver encabezados y cuerpo):

```bash
curl -i http://127.0.0.1:8000/healthz
# Esperado: HTTP/1.1 200 OK y cuerpo JSON {"status": "ok"}
```

Ruff y pruebas automatizadas (local)
-----------------------------------

Ejecuta las comprobaciones de lint/format y las pruebas unitarias con el Python del entorno virtual:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python manage.py check
.venv/bin/python manage.py test
.venv/bin/python -m unittest tests.db.test_db_connection -v
```


Resumen de despliegue en Railway (referencia)
-------------------------------------------

La documentación de despliegue y la verificación post-deploy se mantienen como fuente canónica en
`docs/deployment/railway.md`. Consulte ese archivo para la configuración de build, start command, variables de
entorno y pasos de validación en Railway.

Validación pública del health check
----------------------------------

El contrato del health check es canónico en `specs/001-project-foundation/contracts/health-check.md`.
Puede usar el siguiente comando para comprobar el endpoint público (o local):

```bash
curl -i https://kronolearn-production.up.railway.app/healthz
# Consulte `specs/001-project-foundation/contracts/health-check.md` para el cuerpo JSON esperado y criterios de aceptación.
```

Referencias canónicas
---------------------

- `specs/001-project-foundation/contracts/health-check.md` — contrato canonical del health check
- `docs/deployment/railway.md` — notas de despliegue en Railway
- `docs/dependencies.md` — política de dependencias reproducibles
- `.env.example` — plantilla de variables de entorno

Notas finales
------------

- Este documento refleja el estado actual del proyecto y las tareas completadas.
- No incluyas secretos ni valores reales en el repositorio. Usa variables de entorno y secretos de la plataforma para production.
- T014 no está marcada como completada en `tasks.md`; esta guía sirve como referencia operativa para implementarla.
