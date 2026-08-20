# research.md

**Propósito**: Documentar decisiones técnicas, preguntas abiertas y referencias para la fase de diseño.

## Decisiones preliminares

- Arquitectura: Monolito modular en Django para cumplir la regla de "Monolito modular" de la constitución.
- Base de datos: PostgreSQL como sistema de producción (conexión a través de `DATABASE_URL` en variables de entorno).
- Servidor de aplicación: Gunicorn como servidor WSGI para producción.
- Archivos estáticos: WhiteNoise para servir assets estáticos en el monolito.
- CI: GitHub Actions para lint, formatting y tests rápidos en CI.
- Deploy: Preparación para Railway; documentar variables de entorno y procesos de build.

## Decisiones y aclaraciones resueltas

- Python: se usará Python 3.14 para la línea base.
- Django: se usará Django 5.2 LTS; durante la implementación se seleccionará la versión patch más reciente
	compatible con Python 3.14.
- Base de datos driver: se usará psycopg (psycopg 3) con soporte binario para desarrollo (por ejemplo,
	`psycopg[binary]`).
- PostgreSQL: la instancia de producción será administrada por Railway (servicio gestionado).
- Gestión de dependencias: todas las dependencias DEBEN ser fijadas mediante un archivo de dependencias
	reproducible (por ejemplo `requirements.txt` con hashes, `poetry.lock` o equivalente). Esto garantiza
	builds reproducibles y cumplimiento de la política de versiones.

## Recursos y referencias

- Django documentation
- PostgreSQL documentation
- Gunicorn and WhiteNoise guides
- Railway deployment docs
