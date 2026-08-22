# Research: Control de tema más sutil e integrado

## Contexto técnico existente relevante

- El control actual (`templates/ui/components/theme_toggle.html`, entregado en `specs/009-dark-mode-toggle`) es un
  `<button class="button button--outline theme-toggle" data-theme-toggle aria-pressed="...">` con un ícono
  (`data-theme-toggle-icon`, 🌙/☀️) y una etiqueta de texto siempre visible (`data-theme-toggle-label`, "Modo
  oscuro"/"Modo claro"), actualizados por `ui/static/js/theme-toggle.js`.
- Las clases `.button`/`.button--outline` heredan estilos del selector global de etiqueta `button` en
  `ui/templates/base.html` (`button, .button { min-height: 44px; min-width: 44px; border: 2px solid var(--border);
  box-shadow: var(--shadow-hard); background: var(--border); color: var(--paper); ... }`), que es exactamente el
  tratamiento "botón de acción" que esta feature debe evitar para el control de tema.
- El mecanismo de aplicación del tema (`data-theme` en `<html>`), la persistencia en `localStorage`
  (`kronolearn:theme`) y la sincronización en tiempo real entre pestañas (evento `storage`) — documentados en
  `specs/009-dark-mode-toggle/research.md` y `contracts/theme-toggle.md` — no cambian con esta feature; solo cambia
  la presentación del control y el mecanismo de nombre accesible.

## Decisión 1: Cómo despojar al botón de su caja sin perder el tamaño mínimo de toque

**Decision**: Añadir una regla `.theme-toggle { border: none; box-shadow: none; background: transparent; color:
var(--ink); padding: 0.5rem; }` que sobreescribe el selector global `button`. Por especificidad CSS, un selector de
clase (`.theme-toggle`) siempre gana sobre un selector de etiqueta (`button`), sin necesidad de `!important` ni de
reordenar reglas. Se conserva `min-height: 44px; min-width: 44px;` explícitamente en la misma regla para no perder
la garantía de área táctil que antes venía heredada de `button`.

**Rationale**: Es el cambio mínimo posible: una sola regla CSS nueva, sin tocar el selector global `button` (que
sigue sirviendo a todos los demás botones de acción sin cambios) y sin introducir un mecanismo de estilos distinto
al ya usado en el proyecto (custom properties + selectores CSS planos).

**Alternatives considered**:
- *Quitar las clases `.button`/`.button--outline` y no añadir nada nuevo*: perdería también `min-height`/
  `min-width`, violando FR-005 (mismo tamaño mínimo de toque).
- *Usar `!important`*: innecesario dado que la especificidad de clase ya gana; añadir `!important` sin necesidad
  contradice la práctica ya establecida en el proyecto (no se usa en ninguna regla existente).

## Decisión 2: Mecanismo de nombre accesible permanente (sin texto visible)

**Decision**: Mover la descripción textual de la acción de un `<span>` visible a un atributo `aria-label` dinámico
en el propio `<button>` (por ejemplo `aria-label="Cambiar a modo oscuro"`), actualizado por
`ui/static/js/theme-toggle.js` en el mismo punto donde ya se actualiza `aria-pressed`.

**Rationale**: `aria-label` es el mecanismo estándar para dar nombre accesible a un control cuyo contenido visible
(un ícono) no lo describe por sí mismo; es exactamente el patrón ya recomendado por las guías de accesibilidad para
"botones de solo ícono" y no requiere ninguna dependencia nueva.

**Alternatives considered**:
- *Mantener el `<span data-theme-toggle-label>` visible pero con `class="sr-only"` de forma permanente*: técnicamente
  cumpliría FR-002, pero duplicaría la fuente de verdad del nombre accesible (el navegador expone como nombre
  accesible tanto el contenido de texto del botón como un `aria-label` si ambos existen, y `aria-label` gana;
  mantener el `<span>` solo para lectores de pantalla sería redundante una vez que existe `aria-label`). Se
  descarta a favor de un único mecanismo.

## Decisión 3: Confirmación textual visible al enfocar/pasar el mouse (FR-003)

**Decision**: Reutilizar el mismo texto dinámico (ahora solo en `aria-label`) también como contenido de un
`<span class="theme-toggle__tooltip" aria-hidden="true">` visualmente oculto en reposo (`opacity: 0; visibility:
hidden;`) y revelado únicamente por CSS puro con `.theme-toggle:hover .theme-toggle__tooltip,
.theme-toggle:focus-visible .theme-toggle__tooltip { opacity: 1; visibility: visible; }`. `theme-toggle.js`
actualiza el `textContent` de este `span` en el mismo punto donde actualiza `aria-label`, pero su visibilidad la
controla el navegador vía CSS, no JavaScript.

**Rationale**: No depender de JavaScript para mostrar/ocultar el tooltip evita una fuente adicional de bugs
(listeners de `mouseenter`/`mouseleave`/`focus`/`blur` duplicando lo que `:hover`/`:focus-visible` ya hacen nativa
y correctamente, incluidos casos límite como perder el foco mientras el mouse sigue encima). `aria-hidden="true"`
evita que un lector de pantalla anuncie el tooltip como contenido aparte del `aria-label` ya expuesto por el botón,
evitando un anuncio duplicado.

**Alternatives considered**:
- *Atributo nativo `title="..."`*: es el tooltip más simple posible, pero su temporización, estilo y aparición
  dependen enteramente del navegador (no es estilizable con los tokens del sistema visual) y en muchos navegadores
  no aparece con el foco de teclado, solo con `hover` del mouse — no cumpliría FR-003 para usuarios de teclado.
- *Tooltip manejado con JavaScript (mostrar/ocultar por eventos)*: más código y más superficie de fallo para un
  resultado idéntico al que ya logra CSS puro con `:hover`/`:focus-visible`.

## Decisión 4: Estilo visual del tooltip revelado

**Decision**: Reutilizar el mismo patrón visual ya establecido por `.eyebrow` (fondo `var(--border)`, texto
`var(--paper)`, `border-radius: var(--border-radius-pill)`, texto pequeño en mayúsculas) para el tooltip, en vez de
inventar un nuevo tratamiento visual.

**Rationale**: Reutiliza un token/patrón ya validado por el sistema de diseño (alto contraste garantizado, porque
`--border`/`--paper` ya se usan invertidos en modo oscuro y claro para ese propósito), en vez de introducir una
combinación de color nueva que tendría que revalidarse en ambos modos.

**Alternatives considered**:
- *Chip con borde 2px negro y fondo blanco (como `.panel`)*: consistente con el lenguaje "brutalista" de cajas con
  borde, pero menos legible como tooltip flotante pequeño y duplica innecesariamente el tratamiento de borde que
  esta feature busca evitar en el propio control.

## Ítems de Technical Context resueltos

No quedan `NEEDS CLARIFICATION`: no se introduce ningún lenguaje, dependencia, ni plataforma nueva. Todo el trabajo
ocurre dentro del CSS y JavaScript ya existentes de `ui/templates/base.html` y `ui/static/js/theme-toggle.js`, y en
el markup de `templates/ui/components/theme_toggle.html`.
