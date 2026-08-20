# Deploying to Railway — baseline notes

Este documento recoge los pasos mínimos para desplegar la línea base de KronoLearn en Railway.

Variables de entorno mínimas (usar `specs/001-project-foundation/.env.example` como plantilla):

- `SECRET_KEY`
- `DATABASE_URL` (cadena de conexión a PostgreSQL)
- `RAILWAY_ENV`

Build & Procfile:

- Railway puede ejecutar un comando `web` para iniciar la aplicación. Para producción se espera un comando similar a:

  `gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT`

- WhiteNoise se usará para servir archivos estáticos; asegurarse de incluir la compilación de assets en el build (por ejemplo, `npm run build` para Tailwind si aplica).

Health check:

- Asegurarse de exponer `/healthz` y que responda HTTP 200 con `{ "status": "ok" }`.

Verificación post-deploy:

1. Desplegar la rama de feature en Railway.
2. Comprobar el endpoint `/healthz` en la URL pública y confirmar HTTP 200.
3. Revisar logs de Railway para errores de migración/arranque.

Notas de seguridad:
- No incluyas credenciales reales en el repositorio. Usa secret env vars en Railway.
