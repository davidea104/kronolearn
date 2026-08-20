# ui/frontend — Frontend integration placeholder

Propósito
---------
El directorio `ui/frontend/` contiene los artefactos y la configuración mínima necesaria para integrar
las librerías de frontend que se usarán dentro del monolito Django de KronoLearn. En esta fase se prepara
la estructura y la documentación operativa; las configuraciones concretas se completarán en tareas posteriores.

Contexto y alcance
------------------
- El frontend forma parte del monolito Django y debe integrarse con la estructura de la aplicación y su pipeline
  de despliegue.
- Esta carpeta actúa como el lugar de trabajo para las dependencias de frontend (herramientas de build, configuración
  de Tailwind, etc.) sin introducir todavía implementaciones ni dependencias.

Ubicaciones previstas en el repositorio
--------------------------------------
- Templates de Django: `ui/templates/`
- JavaScript (assets fuente): `ui/static/js/`
- CSS (assets fuente): `ui/static/css/`
- Espacio de trabajo frontend / package.json: `ui/frontend/`

Roles de las tecnologías previstas
---------------------------------

- HTMX
  - Manejará interacciones con el servidor desde el HTML (peticiones parciales, gestión de swaps y triggers).
  - Se espera usar HTMX para reducir la necesidad de SPAs y preservar la lógica de servidor en el monolito.
- Alpine.js
  - Manejará microinteracciones y comportamiento declarativo en el DOM (estado local, toggles, pequeñas UI reactions).
  - Ideal para patrones ligeros dentro de templates sin construir aplicaciones en JavaScript complejas.
- Tailwind CSS
  - Gestión de la presentación mediante utilidades CSS y un pipeline de construcción para generar el CSS final.
  - El CSS generado se colocará en `ui/static/css/` y, en producción, será servido como parte de los assets estáticos.

Producción y serving de archivos estáticos
-----------------------------------------
- En producción los archivos estáticos serán recolectados por `collectstatic` y servidos por WhiteNoise (ver `docs/gunicorn-whitenoise.md`).
- El flujo exacto de build y coleccionado de activos se definirá en las tareas siguientes (T021, T022, T023).

Estado y próximos pasos (tareas relacionadas)
--------------------------------------------
- Las configuraciones específicas se implementarán en:
  - T021 — configuración / documentación HTMX
  - T022 — configuración / documentación Alpine.js
  - T023 — configuración / documentación Tailwind CSS (build pipeline, integración con collectstatic)
- Por ahora `ui/frontend/` contiene un `package.json` placeholder (sin dependencias ni scripts). No ejecutar `npm install` aún.

Referencias
----------
- `docs/gunicorn-whitenoise.md` — notas sobre servir assets en producción con WhiteNoise
- `specs/001-project-foundation/plan.md` — plan técnico para Project Foundation
- `.specify/memory/constitution.md` — constitución del proyecto (normas y principios a respetar)
