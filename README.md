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

1. Copiar `specs/001-project-foundation/.env.example` a `.env` y rellenar variables necesarias (no incluir secretos en el repo).
2. Crear un entorno virtual de Python e instalar dependencias (ver `docs/dependencies.md`).
3. Ejecutar servidores de desarrollo según la documentación del plan (`specs/001-project-foundation/quickstart.md`).

Notas de seguridad y constitución:
- Nunca guardar secretos reales en el repositorio. Use variables de entorno para claves y credenciales.
- Las decisiones de diseño deben respetar la `constitution` en `.specify/memory/constitution.md` (pruebas, idempotencia, seguridad por defecto).
