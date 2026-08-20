# HTMX integration notes — ui/frontend

Propósito
---------

Este documento describe el uso sugerido de HTMX dentro del monolito Django de KronoLearn. Está limitado a la
integración conceptual y ejemplos de atributos `hx-*` para templates ubicados en `ui/templates/`.

Alcance
-------

Cobertura: interacción HTMX en plantillas server-rendered, rutas de ejemplo y patrones recomendados. No incluye
implementación de Alpine.js ni Tailwind CSS (estas se cubren en T022 y T023 respectivamente).

Ubicación de templates
----------------------

Los templates que usarán HTMX se colocarán bajo:

- `ui/templates/`

Principios de uso sugeridos
---------------------------

- Preferir peticiones parciales desde HTMX para zonas actualizables (por ejemplo: lista de items, contador de puntos,
  fragmentos de progreso) en lugar de recargar la página completa.
- Mantener la lógica de negocio en el servidor; HTMX debe solicitar fragmentos HTML que el servidor renderiza.
- Diseñar endpoints que devuelvan fragmentos HTML (templates parciales) y estados HTTP apropiados.

Rutas de ejemplo y contratos ligeros
----------------------------------

1) Actualizar la lista de actividades del usuario

- Ruta (GET): `/ui/activities/fragment/` — devuelve un fragmento HTML con la lista de actividades recientes.
- Uso en template padre (`ui/templates/dashboard.html`):

```html
<div id="activities" hx-get="/ui/activities/fragment/" hx-trigger="load" hx-swap="innerHTML">
  <!-- Placeholder content mientras se carga -->
  <div class="placeholder">Cargando actividades...</div>
</div>
```

2) Marcar un elemento como completado (acción POST) y actualizar el fragmento

- Ruta (POST): `/ui/activity/<int:pk>/complete/` — procesa la acción y devuelve el fragmento actualizado de la lista.
- Ejemplo en template (`ui/templates/activity_item.html`):

```html
<button hx-post="/ui/activity/123/complete/" hx-swap="outerHTML" hx-target="#activity-123">
  Marcar como completado
</button>

<div id="activity-123">
  <!-- contenido del item -->
</div>
```

3) Formularios de comentario en línea (enviar y reemplazar sección)

- Ruta (POST): `/ui/activity/<int:pk>/comment/` — procesa el comentario y devuelve el fragmento del hilo de comentarios.
- Atributos sugeridos: `hx-post`, `hx-target`, `hx-swap`, `hx-vals` cuando se necesite enviar datos adicionales.

Ejemplos de atributos `hx-*` usados y su propósito
-------------------------------------------------

- `hx-get="/ruta/"` — realizar una petición GET a la ruta especificada.
- `hx-post="/ruta/"` — realizar una petición POST.
- `hx-trigger="event"` — evento que dispara la petición (ej.: `click`, `load`, `change`, `submit`).
- `hx-swap="innerHTML|outerHTML|afterbegin|beforeend"` — cómo aplicar la respuesta en el DOM.
- `hx-target="#selector"` — selector CSS para el elemento objetivo a actualizar.
- `hx-vals` — incluir valores adicionales en la petición (cuando no se usan formularios estándar).

Buenas prácticas
----------------

- Keep fragments small: renderizar fragmentos parciales que sean fáciles de testear y cachear.
- Use progressive enhancement: los enlaces y formularios deben funcionar sin JavaScript cuando sea posible.
- Return proper HTTP status codes: 200 para éxito con fragmento HTML; 204/202 si no hay contenido para actualizar.
- CSRF: usar los mecanismos de Django para tokens CSRF en peticiones POST — incluir token en los formularios o via headers.

Integración con rutas y pruebas
------------------------------

- Endpoints utilizados por HTMX deben tener tests unitarios/funcionales que verifiquen tanto la respuesta HTML fragmentada
  como los efectos secundarios (por ejemplo, marcar actividad como completada).
- Definir convenciones para nombres de templates parciales (ej.: `*_fragment.html`) para facilitar su localización.

Ejemplo de fragment template (`ui/templates/activities_fragment.html`)

```html
<ul>
  {% for activity in activities %}
    <li id="activity-{{ activity.id }}">{{ activity.title }}</li>
  {% endfor %}
</ul>
```

Seguridad
---------

- Validar entradas en el servidor y aplicar CSRF protection en POSTs.
- Evitar exponer datos sensibles en fragmentos HTML directamente; preferir llamadas que devuelvan solo lo necesario.

Notas finales
------------

- Este documento es una guía inicial (T021). La configuración concreta de HTMX en producción y su integración con
  Alpine.js y Tailwind CSS se desarrollará en tareas posteriores (T022, T023).
