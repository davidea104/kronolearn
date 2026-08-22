# Deploying to Railway — baseline notes

Este documento recoge los pasos mínimos para desplegar la línea base de KronoLearn en Railway.

Variables de entorno mínimas (usar `.env.example`, ubicado en la raíz del repositorio, como plantilla):

- `SECRET_KEY`
- `DATABASE_URL` (cadena de conexión a PostgreSQL)
- `RAILWAY_ENV`
- `DEBUG=False`
- `DJANGO_SETTINGS_MODULE=kronolearn.settings.production`
- `ALLOWED_HOSTS=kronolearn-production.up.railway.app`
- `LOGIN_TRUSTED_PROXY_COUNT=1` para la topologia normal de un proxy de Railway; ajustar solo si se agrega o retira un proxy confiable delante de la aplicacion.
- `CONTENT_AUTHOR_ACCOUNT_ID` con la referencia privada de una cuenta activa que ya tenga el rol `content_admin`; no registrar ni imprimir su valor.

Build & Procfile:

- Railway puede ejecutar un comando `web` para iniciar la aplicación. Para producción se espera un comando similar a:

  `gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT`

- WhiteNoise se usará para servir archivos estáticos; asegurarse de incluir la compilación de assets en el build (por ejemplo, `npm run build` para Tailwind si aplica).

Pre-Deploy Command:

- Provisionar la cuenta autora y asignarle `content_admin` antes del primer despliegue que cargue contenido.
- Configurar en Railway un unico comando que aplique migraciones y, solo si tienen exito, reconcilie el corpus publicado:

  `python manage.py migrate --noinput && python manage.py load_learning_content`

- No ejecutar `load_learning_content` desde el Start Command. La carga es atomica e idempotente, pero pertenece al despliegue y debe terminar antes de iniciar Gunicorn.
- Si falta la configuracion autora o la cuenta no esta autorizada, el pre-deploy debe fallar de forma generica y el proceso web no debe arrancar con una carga parcial.

Health check:

- Asegurarse de exponer `/healthz` y que responda HTTP 200 con `{ "status": "ok" }`.

Verificación post-deploy:

1. Desplegar la rama de feature en Railway.
2. Comprobar el endpoint `/healthz` en la URL pública y confirmar HTTP 200.
3. Revisar logs de Railway para errores de migración/arranque.

Notas de seguridad:
- No incluyas credenciales reales en el repositorio. Usa secret env vars en Railway.

## Resultado del primer despliegue

- Fecha de validación: 2026-08-20
- Entorno: Railway
- Rama desplegada: `feature/HU-00-project-foundation`
- Servicio web: `kronolearn`
- Base de datos: PostgreSQL administrado por Railway
- Dominio: kronolearn-production.up.railway.app
- Health check: kronolearn-production.up.railway.app/healthz
- Resultado: HTTP 200
- Respuesta: `{"status": "ok"}`
- Build: exitoso
- Migraciones: ejecutadas mediante Pre-Deploy Command
- Gunicorn: activo
- PostgreSQL: conectado mediante referencia `DATABASE_URL`
- Target Port de Railway: `8080`
- Build Command: `python manage.py collectstatic --noinput`
- Pre-Deploy Command: `python manage.py migrate --noinput`
- Start Command: `gunicorn kronolearn.wsgi:application --bind 0.0.0.0:$PORT`
