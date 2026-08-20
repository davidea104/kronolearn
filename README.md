# kronolearn
Plataforma de microlearning gamificado desarrollada con Django y Spec Kit.

Este repositorio contiene la línea base (baseline) para el monolito modular de KronoLearn.

Fase actual: Project Foundation (estructura, variables de entorno, contratos básicos y documentación de despliegue).

Archivos y directorios relevantes:

- `specs/001-project-foundation/` — especificación, plan y tareas para la base del proyecto.
- `specs/001-project-foundation/contracts/health-check.md` — contrato canonical del endpoint de health check (`/healthz`).
- `specs/001-project-foundation/.env.example` — variables de entorno mínimas de ejemplo.
- `docs/deployment/railway.md` — pasos y notas para desplegar en Railway (documental).
- `docs/dependencies.md` — política de dependencias reproducibles y formato esperado (`requirements.txt` o `poetry.lock`).

Cómo usar (desarrollo local mínimo):

1. Copiar `.env.example` a `.env` y rellenar variables necesarias (no incluir secretos en el repo).
2. Crear un entorno virtual de Python e instalar dependencias (ver `docs/dependencies.md`).
3. Exportar las variables desde el shell y ejecutar Django con PostgreSQL:

   ```sh
   set -a; source .env; set +a
   export DJANGO_SETTINGS_MODULE=kronolearn.settings.development
   .venv/bin/python manage.py check
   .venv/bin/python manage.py runserver
   ```

   El proyecto no usa SQLite: `DATABASE_URL` debe apuntar a PostgreSQL en todos los entornos.

Notas de seguridad y constitución:
- Nunca guardar secretos reales en el repositorio. Use variables de entorno para claves y credenciales.
- Las decisiones de diseño deben respetar la `constitution` en `.specify/memory/constitution.md` (pruebas, idempotencia, seguridad por defecto).
