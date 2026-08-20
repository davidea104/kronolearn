# Alpine.js integration notes — ui/frontend

Propósito
---------

Guía mínima para incluir y usar Alpine.js dentro del monolito Django de KronoLearn. Este documento ofrece
patrones recomendados, ubicaciones de archivos y ejemplos de uso con atributos de Alpine.js. Está limitado a
la fase T022 y no implementa Tailwind ni HTMX (HTMX cubierto en T021).

Ubicación recomendada para JavaScript propio
--------------------------------------------

Los archivos JavaScript propios deben ubicarse en:

- `ui/static/js/`

Incluir Alpine.js en el template base
------------------------------------

Se recomienda agregar la inclusión de Alpine.js en el template base del proyecto (por ejemplo `ui/templates/base.html`).
La inclusión puede ser gestionada por el equipo en fases posteriores; aquí se documenta el patrón de referencia sin
incluir CDN o versiones concretas.

Patrón recomendado
------------------

- Mantener el markup declarativo: usar atributos `x-data`, `x-show`, `x-model`, `x-on` (o la forma abreviada `@click`) en
  los templates server-rendered.
- Separar el JavaScript propio en archivos dentro de `ui/static/js/` y enlazarlos desde el template base cuando sea necesario.

Ejemplos sencillos
------------------

1) Toggle simple usando `x-data` y `x-show`

```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle detalles</button>
  <div x-show="open">
    <p>Detalles expandibles aquí.</p>
  </div>
</div>
```

2) Formulario con `x-model` y envío progresivo

```html
<div x-data="{ message: '' }">
  <input type="text" x-model="message" placeholder="Escribe...">
  <p>Preview: <span x-text="message"></span></p>
</div>
```

3) Manejar evento con `x-on` / `@click` y llamar a función definida en archivo JS propio

Template:

```html
<div x-data>
  <button @click="window.myFrontend.toggleFeature()">Activar feature</button>
</div>
```

Archivo JS propio (ejemplo en `ui/static/js/frontend.js`):

```javascript
window.myFrontend = {
  toggleFeature() {
    // lógica simple de ejemplo
    console.log('Feature toggled')
  }
}
```

Cómo incluir JavaScript propio desde el template base
-----------------------------------------------------

En el `base.html` (o template layout principal) enlazar los assets estáticos generados o los archivos fuente durante
desarrollo. Ejemplo conceptual (sin rutas exactas ni comandos de build):

```html
<!-- al final del body -->
<script src="{% static 'js/frontend.js' %}"></script>
```

Seguridad y accesibilidad
-------------------------

- Seguridad: validar y sanear entradas en el servidor; no confiar en el estado del cliente para autorizaciones.
- CSRF: para peticiones que involucren cambios, usar los mecanismos de CSRF de Django (incluir token en formularios
  o en headers cuando sea necesario).
- Accesibilidad: asegurar que elementos interactivos sean accesibles por teclado y tengan roles/atributos ARIA cuando
  correspondan (ej.: `aria-expanded` sincronizado con estados de `x-show`).

Pruebas y recomendaciones de QA
------------------------------

- Los componentes ligeros que usan Alpine.js pueden probarse mediante pruebas end-to-end o pruebas de integración
  que verifiquen el comportamiento visible (ej.: toggle muestra/oculta contenido, actualización de preview).
- Mantener los handlers simples y delegar lógica compleja al servidor o a módulos JS bien testeados.

Notas finales
------------

- Este documento cubre T022 únicamente. No se crean archivos adicionales fuera de `ui/static/js/` salvo cuando el
  equipo acuerde y autorice implementar assets adicionales.
