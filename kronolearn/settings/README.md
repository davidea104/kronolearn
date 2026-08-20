# Settings por entorno

La configuración de KronoLearn se organiza como un paquete `kronolearn.settings` para separar valores comunes de los
valores específicos de cada entorno. Esta tarea define la estructura; los módulos de settings ejecutables se crearán
cuando se inicialice el proyecto Django, sin adelantar el endpoint de health check ni la configuración de base de datos.

## Estructura prevista

```text
kronolearn/settings/
├── __init__.py
├── base.py
├── development.py
└── production.py
```

- `base.py`: configuración compartida y segura por defecto: apps instaladas, middleware, plantillas, internacionalización,
  estáticos y valores comunes.
- `development.py`: extiende `base.py`; permite herramientas locales y exige una configuración explícita de desarrollo.
- `production.py`: extiende `base.py`; exige los secretos y hosts permitidos, desactiva `DEBUG` y contiene los ajustes de
  Gunicorn, WhiteNoise y PostgreSQL que correspondan.

`__init__.py` no debe seleccionar un entorno de forma implícita. El proceso de arranque seleccionará el módulo mediante
`DJANGO_SETTINGS_MODULE`, por ejemplo `kronolearn.settings.development` o `kronolearn.settings.production`.

## Variables de entorno

Los settings leen únicamente variables de entorno del proceso. `.env` es una conveniencia local y nunca se versiona;
Railway proporciona las variables en el entorno de ejecución. La plantilla canónica disponible hoy es
`specs/001-project-foundation/.env.example`.

| Variable | Entornos | Regla prevista |
| --- | --- | --- |
| `SECRET_KEY` | todos | obligatoria; no se admite valor por defecto en producción. |
| `DEBUG` | todos | se interpreta explícitamente como booleano; debe ser `False` en producción. |
| `DATABASE_URL` | desarrollo y producción | será obligatoria cuando se implemente la conexión PostgreSQL (T011). |
| `ALLOWED_HOSTS` | producción | lista explícita de hosts permitidos; no usar comodines. |
| `PORT` | producción | provista por Railway y usada por Gunicorn; no se persiste como secreto. |
| `RAILWAY_ENV` | Railway | identifica el entorno de despliegue; no autoriza cambios de seguridad por sí sola. |

## Validación y precedencia

1. El sistema operativo o Railway proporcionan las variables al proceso.
2. En desarrollo, una herramienta de carga de `.env` podrá poblar solo variables ausentes; nunca debe sobrescribir
   variables ya definidas por el proceso.
3. Al cargar settings, los valores obligatorios se validarán y los booleanos/listas se parsearán de forma estricta.
4. Un valor faltante o malformado debe detener el arranque con un mensaje que identifique la variable, sin mostrar su
   contenido ni secretos.

Las variables no deben leerse desde vistas, templates ni JavaScript. La configuración se concentra en el paquete de
settings y los servicios de dominio no reciben secretos desde el navegador.
