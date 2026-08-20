# Gunicorn y WhiteNoise

Este documento define el contrato operativo de producción para la línea base. No implementa aún settings, WSGI ni
el endpoint `/healthz`.

## Arranque en Railway

El proceso `web` deberá usar Gunicorn y el puerto inyectado por Railway:

```sh
gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT
```

El comando se ejecutará desde la raíz del repositorio, con `DJANGO_SETTINGS_MODULE` apuntando a
`kronolearn.settings.production`. Railway debe proveer `PORT`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` y las
variables de entorno declaradas en la plantilla del proyecto. No se incluyen secretos en comandos, código ni archivos
versionados.

Antes de usar este comando se deberán crear `kronolearn/wsgi.py` y los settings ejecutables como parte de la
inicialización de Django; no son parte de T008.

## Estrategia de archivos estáticos

WhiteNoise se integrará en el middleware de Django, inmediatamente después de `SecurityMiddleware`, y servirá los
archivos recolectados en `STATIC_ROOT`. El flujo de despliegue previsto es:

1. Compilar los assets del monolito cuando exista el pipeline frontend.
2. Ejecutar `python3 manage.py collectstatic --noinput` durante el build de Railway.
3. Publicar el artefacto recolectado con WhiteNoise desde el mismo proceso Gunicorn.

La configuración de producción usará almacenamiento comprimido y con nombres versionados para permitir caché segura de
assets inmutables. Los archivos cargados por usuarios no se servirán con WhiteNoise; su estrategia se decidirá cuando
esa funcionalidad entre en alcance.

## Límites de esta fase

- No se crea un `Procfile` ni un workflow de CI (T009).
- No se configura ni prueba PostgreSQL (T011).
- No se implementa el endpoint `/healthz`.
