# Gunicorn y WhiteNoise

Este documento define el contrato operativo de producción para la línea base. Los settings y WSGI están
implementados en el proyecto; la definición y los criterios del endpoint de health check se encuentran en el
contrato canonical `specs/001-project-foundation/contracts/health-check.md` y las comprobaciones automatizadas
en `tests/smoke/test_health_check.py`.

## Arranque en Railway

El proceso `web` deberá usar Gunicorn y el puerto inyectado por Railway:

```sh
gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT
```

El comando se ejecutará desde la raíz del repositorio, con `DJANGO_SETTINGS_MODULE` apuntando a
`kronolearn.settings.production`. Railway debe proveer `PORT`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` y las
variables de entorno declaradas en la plantilla del proyecto. No se incluyen secretos en comandos, código ni archivos
versionados.

- El workflow de CI está implementado y validado mediante el PR #1.
- PostgreSQL está configurado y validado localmente.
- El endpoint `/healthz` está definido por el contrato canonical y validado mediante pruebas smoke y en los despliegues documentados (ver `specs/001-project-foundation/contracts/health-check.md` y `docs/deployment/railway.md`).

## Estrategia de archivos estáticos

WhiteNoise se integrará en el middleware de Django, inmediatamente después de `SecurityMiddleware`, y servirá los
archivos recolectados en `STATIC_ROOT`. El flujo de despliegue previsto es:

1. Compilar los assets del monolito cuando exista el pipeline frontend.
2. Ejecutar `python3 manage.py collectstatic --noinput` durante el build de Railway.
3. Publicar el artefacto recolectado con WhiteNoise desde el mismo proceso Gunicorn.

La configuración de producción usará almacenamiento comprimido y con nombres versionados para permitir caché segura de
assets inmutables. Los archivos cargados por usuarios no se servirán con WhiteNoise; su estrategia se decidirá cuando
esa funcionalidad entre en alcance.

## Estado y referencias

- Consulte `specs/001-project-foundation/contracts/health-check.md` para el contrato canonical de `/healthz`.
- Consulte `docs/deployment/railway.md` para los pasos de despliegue, variables de entorno y verificación post-deploy en Railway.
- Las pruebas de health check y la verificación de despliegue se documentan en los archivos mencionados y se ejecutan
	como parte del pipeline de validación establecido en CI.
