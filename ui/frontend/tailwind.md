# Tailwind CSS integration — ui/frontend

Fecha: 2026-08-20
Alcance: T023 — instrucción y ejemplos para integrar Tailwind CSS en el monolito Django (Project Foundation).

Resumen
-------

Este documento describe la configuración y el pipeline recomendado para integrar Tailwind CSS en el monolito
KronoLearn. Proporciona ejemplos de configuración (`tailwind.config.js`, `postcss.config.js`), define rutas de
contenido para escanear clases dentro de `ui/templates/`, y detalla el flujo de build y la ubicación del CSS
compilado que será servido por WhiteNoise.

Nota importante
--------------

- No se crean archivos reales de configuración en esta tarea; los ejemplos se incluyen aquí como contenido
  documentado (`tailwind.config.js` y `postcss.config.js` mostrados como ejemplo). Si el equipo desea que los
  archivos sean añadidos, autorizad explícitamente la creación.
- El `package.json` actual en `ui/frontend/` es mínimo y no contiene scripts. A continuación se proponen scripts
  compatibles que el equipo puede añadir manualmente al `package.json` si se decide. (No modifico `package.json`
  automáticamente; ver la sección correspondiente.)

1) Rutas de contenido para Tailwind
-----------------------------------

Tailwind necesita conocer las rutas donde buscar clases utilizadas en HTML/JS/TS/模板. Para este monolito, las rutas
relevantes incluyen:

- `ui/templates/**/*.html`
- `kronolearn/templates/**/*.html` (si existen templates compartidos en esa ruta)
- `ui/static/js/**/*.js` (si se usan clases desde JS dinamicamente)

Ejemplo de `tailwind.config.js` (documentado)
--------------------------------------------

```js
module.exports = {
  content: [
    './ui/templates/**/*.html',
    './kronolearn/templates/**/*.html',
    './ui/static/js/**/*.js'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Notas sobre `content`:

- Ajustar las rutas si el equipo usa una convención distinta. El patrón `**/*.html` asegura que Tailwind escanee
  todos los templates dentro de `ui/templates/`.

2) `postcss.config.js` (documentado)
------------------------------------

PostCSS se utiliza normalmente para aplicar Tailwind y autoprefixer en el pipeline de build.

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
```

3) Archivo CSS de entrada recomendado y salida compilada
-------------------------------------------------------

- Archivo de entrada (fuente): `ui/frontend/src/styles/tailwind.css`
  - Contenido mínimo recomendado en `tailwind.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- Archivo CSS compilado (salida): `ui/static/css/tailwind.css`
  - En producción, este archivo será recolectado por `collectstatic` y servido por WhiteNoise.

4) Ejemplo de scripts npm (propuestos, compatibles con el package.json actual)
-----------------------------------------------------------------------------

El `package.json` actual en `ui/frontend/` es mínimo y no contiene scripts. A continuación se muestran scripts que
pueden añadirse por el equipo a `ui/frontend/package.json` cuando lo consideren adecuado. No los añado automáticamente
sin autorización.

- Scripts propuestos para desarrollo y producción:

```json
"scripts": {
  "build:css": "postcss ui/frontend/src/styles/tailwind.css -o ui/static/css/tailwind.css",
  "watch:css": "postcss ui/frontend/src/styles/tailwind.css -o ui/static/css/tailwind.css --watch",
  "build:css:prod": "NODE_ENV=production postcss ui/frontend/src/styles/tailwind.css -o ui/static/css/tailwind.css --env production"
}
```

Explicación:

- `build:css` — compila el CSS durante desarrollo/CI (no minificado por defecto).
- `watch:css` — observa cambios y recompila automáticamente durante desarrollo.
- `build:css:prod` — compila una versión optimizada para producción (poner `NODE_ENV=production` o usar
  herramientas de minificación adicionales según la cadena de herramientas elegida).

Compatibilidad con el `package.json` actual
------------------------------------------

- El `package.json` mínimo actual contiene solo `name` y `private` y no impide añadir los scripts anteriores.
- Si el equipo decide añadir los scripts, hágalo manualmente en `ui/frontend/package.json` o autorice al equipo
  a realizar el cambio. No lo modifico automáticamente porque la spec no lo solicita explícitamente para esta tarea.

5) Integración con WhiteNoise y `collectstatic`
----------------------------------------------

- En producción, Django `collectstatic` recopilará los archivos estáticos desde las rutas configuradas (asegurarse de
  que `ui/static/` esté incluido en `STATICFILES_DIRS`). El CSS compilado debe estar en `ui/static/css/tailwind.css` para
  ser recolectado.
- WhiteNoise servirá los assets estáticos recogidos por `collectstatic`. Asegúrese de que el `Start Command` en Railway
  (o el proceso de build) ejecuta `python manage.py collectstatic --noinput` antes de iniciar Gunicorn.

6) Recomendaciones para desarrollo local, CI y Railway
-----------------------------------------------------

- Desarrollo local:
  - Usar `watch:css` para recompilar durante desarrollo.
  - Mantener `ui/frontend/src/styles/tailwind.css` como fuente única del CSS.
  - Servir con `runserver` y usar `collectstatic` ocasionalmente para comprobar el resultado final de assets.

- CI (GitHub Actions):
  - Añadir un paso en el pipeline CI para ejecutar `build:css` antes de probar o empaquetar el artefacto, por ejemplo
    dentro del job `ci` o un job separado `assets`.
  - Esto requiere que el runner tenga Node.js y PostCSS/Tailwind instalados (añadir steps de setup en `.github/workflows/ci.yml`).

- Railway (producción):
  - Durante build, ejecutar `npm ci` (o `npm install`) en `ui/frontend/` y ejecutar `npm run build:css` antes de
    `python manage.py collectstatic --noinput`.
  - Alternativa: compilar CSS fuera de Railway y subir los assets ya compilados a la rama si prefieres evitar Node en Railway.

7) Seguridad y optimización
---------------------------

- En `build:css:prod`, activar Purge/Content scanning (Tailwind JIT / purge) para eliminar clases no usadas y reducir
  el tamaño del CSS final.
- Evitar inline styles que contengan datos sensibles; compilar y servir assets estáticos a través de WhiteNoise.

8) Consideraciones finales
--------------------------

- Si el equipo autoriza, puedo añadir los scripts propuestos al `package.json` y/o crear un scaffold mínimo de
  `ui/frontend/src/styles/tailwind.css`. Por ahora solo he documentado las configuraciones y el pipeline.
- No se ha creado ningún archivo de configuración real (`tailwind.config.js` ni `postcss.config.js`) por restricción.

---

Confirmación de límites
-----------------------

- Archivos creados: `ui/frontend/tailwind.md` (documento generado por T023).
- Archivos modificados: `specs/001-project-foundation/tasks.md` — cambiada la casilla de T023 a [x].
- No se han creado `tailwind.config.js`, `postcss.config.js`, ni archivos CSS o JS reales.
- T024 y tareas posteriores no fueron modificadas.
