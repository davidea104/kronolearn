# quickstart.md

**Objetivo**: Guía mínima para validar localmente la preparación técnica sin incluir código.

## Prerrequisitos

- Acceso a un entorno Python (versión a definir).
- PostgreSQL disponible (local o remoto) y `DATABASE_URL` configurada.
- Permisos de GitHub para configurar Actions y acceso a Railway.

**Decisiones de versión**:

- Python 3.14
- Django 5.2 LTS (usar la versión patch más reciente compatible)
- psycopg 3 con soporte binario (`psycopg[binary]`)

**Dependencias reproducibles**: Verificar que el repositorio incluya un archivo de dependencias reproducible
(por ejemplo `requirements.txt` con hashes o `poetry.lock`).

## Validaciones mínimas a realizar

1. Documentar y comprobar que el README contiene instrucciones para arrancar en modo desarrollo.
2. Verificar que el contract del health check está documentado y que la ruta, método y respuesta esperada están listadas.
3. Comprobar que existe documentación para ejecutar Gunicorn en producción (comando esperado) y servir estáticos con WhiteNoise.
4. Ejecutar el pipeline de GitHub Actions (simulado o en un branch) y verificar que lint + formatting + tests rápidos se ejecutan.
5. Verificar que la documentación para desplegar en Railway incluye las variables de entorno mínimas y pasos de build.

## Resultado esperado

- Lista de comprobaciones con OK/FAIL que confirmen la preparación para despliegue.
