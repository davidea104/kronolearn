# Uso y diagnóstico de CI

Este documento explica qué valida el workflow de CI, cómo reproducir las comprobaciones localmente, cómo interpretar
salidas y cómo diagnosticar fallos comunes.

Qué valida el workflow
----------------------

El workflow `.github/workflows/ci.yml` ejecuta, en orden, las siguientes comprobaciones:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

Cuándo se ejecuta
-----------------

- En `pull_request` hacia `main`.
- En `push` hacia `main`.

Requisitos para ejecutar las comprobaciones localmente
---------------------------------------------------

- Python 3.14 (o compatible con la línea base del proyecto).
- pip
- PostgreSQL 16 corriendo localmente.
- Un entorno virtual con las dependencias instaladas desde `requirements.txt`.

Crear y activar `.venv`
-----------------------

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar `requirements.txt`
--------------------------

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Crear `.env` desde `.env.example` y cargar variables
--------------------------------------------------

```bash
cp .env.example .env
set -a
source .env
set +a
```

Selección de configuración de Django (desarrollo)
-------------------------------------------------

```bash
export DJANGO_SETTINGS_MODULE=kronolearn.settings.development
export DEBUG=True
```

Comprobaciones locales (orden)
-----------------------------

Ejecuta los pasos en el siguiente orden para reproducir el comportamiento del CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

Verificar PostgreSQL local (macOS)
---------------------------------

```bash
brew services list | grep postgresql
```

Interpretación de códigos de salida
----------------------------------

- Exit code 0: paso correcto.
- Exit code != 0: paso fallido; CI considerará el job como fallido y parará la ejecución del pipeline.

Diagnóstico de fallos comunes
----------------------------

- Ruff (lint):
  - Síntomas: salida con errores y rutas de fichero.
  - Acción: ejecutar `.venv/bin/ruff check .` localmente y corregir las fallas; para aplicar formato usar `.venv/bin/ruff format .` y luego volver a revisar con `ruff format --check .`.

- Ruff format --check:
  - Síntomas: archivos que no cumplen el formato.
  - Acción: `.venv/bin/ruff format .` y commitear los cambios.

- `manage.py check`:
  - Síntomas: errores de configuración o imports.
  - Acción: asegúrate de que `DJANGO_SETTINGS_MODULE` apunta a `kronolearn.settings.development`, que las dependencias están instaladas y que los módulos necesarios existen.

- `makemigrations --check --dry-run`:
  - Síntomas: exit code != 0 indica modelos con cambios sin migraciones.
  - Acción: generar migraciones en la rama correspondiente y volver a ejecutar la comprobación.

- Tests unitarios (`manage.py test`):
  - Síntomas: fallos con tracebacks.
  - Acción: ejecutar los tests en modo verbose y aislar el test problemático.
  - Ejemplo para ejecutar un módulo concreto:

```bash
.venv/bin/python manage.py test tests.smoke.test_health_check
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

- Fallos de PostgreSQL / tests.db.test_db_connection:
  - Síntomas: errores de conexión, timeouts o autenticación.
  - Acción:
    - Verifica que PostgreSQL 16 está corriendo localmente.
    - Verifica que `DATABASE_URL` en `.env` coincide con las credenciales locales.
    - Reintenta las pruebas tras confirmar que el servicio DB responde.

Revisar logs de GitHub Actions
-----------------------------

- En GitHub: Repo -> Actions -> seleccionar el workflow run -> seleccionar el job -> revisar el step y sus logs (stdout/stderr).
- Copiar fragmentos relevantes para reproducir localmente.
- Usar la opción "Re-run jobs" en la UI para reintentos rápidos si procede.

Volver a ejecutar CI mediante un nuevo push
-----------------------------------------

- Hacer cambios locales, commit y push a la rama del PR. GitHub ejecutará de nuevo los triggers (pull_request/push).
- Alternativa: usar "Re-run jobs" desde la UI de Actions.

Políticas importantes
--------------------

- No usar `--no-verify`, `|| true` ni omitir pruebas para forzar una integración.
- No exponer SECRET_KEY, DATABASE_URL ni otras credenciales en los logs ni en commits.
- Un merge hacia `main` solo debe realizarse si CI está en verde y tras revisión manual del diff.

Referencias
----------

- `.github/workflows/ci.yml`
- `specs/001-project-foundation/tests-strategy.md`
- `docs/dependencies.md`
- `docs/db-railway.md`

Notas finales
-------------

Este documento describe cómo reproducir localmente las comprobaciones del pipeline de CI, cómo interpretar sus salidas
y cómo diagnosticar las fallas más comunes. No incluimos ni mostramos secretos ni valores reales en este documento.
