# UI Contract: Presentación sutil del control de cambio de tema

Este contrato **reemplaza** la sección de accesibilidad y el markup interno descritos en
`specs/009-dark-mode-toggle/contracts/theme-toggle.md` para `templates/ui/components/theme_toggle.html`. Todo lo
demás de ese contrato (atributo `data-theme`, almacenamiento en `localStorage`, sincronización entre pestañas vía
evento `storage`, alcance de páginas) permanece vigente sin cambios.

## Markup interno (actualizado)

```html
<button type="button" class="theme-toggle" data-theme-toggle aria-pressed="false" aria-label="Cambiar a modo oscuro">
  <span class="theme-toggle__icon" aria-hidden="true" data-theme-toggle-icon>🌙</span>
  <span class="theme-toggle__tooltip" aria-hidden="true" data-theme-toggle-label>Modo oscuro</span>
</button>
```

Cambios respecto a `009`:
- Ya no lleva las clases `.button`/`.button--outline` (evita heredar borde, sombra dura y fondo sólido).
- Añade `aria-label`, fuente única del nombre accesible (ver Decisión 2 de `research.md`).
- El `<span data-theme-toggle-label>` pasa a ser un tooltip visualmente oculto en reposo (`.theme-toggle__tooltip`,
  `aria-hidden="true"`), no un texto siempre visible.

## Contrato visual

| Estado | Tratamiento |
|---|---|
| Reposo | Sin borde, sin sombra, fondo transparente; solo el ícono es visible. Área mínima de toque: 44×44px (sin cambios respecto a 009). |
| `:hover` / `:focus-visible` | Fondo `var(--divider)` como única señal de interactividad, más el tooltip revelado (ver abajo). El foco visible global (`outline: 2px solid var(--border)`) se mantiene sin cambios. |
| Tooltip revelado | Aparece por CSS puro (sin JavaScript) al recibir `:hover` o `:focus-visible`; estilo idéntico al patrón ya usado por `.eyebrow` (fondo `var(--border)`, texto `var(--paper)`, píldora). |

## Contrato de accesibilidad (actualizado)

- El nombre accesible del control es **siempre** el `aria-label` del `<button>`, nunca el contenido del tooltip
  (marcado `aria-hidden="true"` para evitar un anuncio duplicado).
- `aria-label` y `aria-pressed` DEBEN actualizarse en el mismo punto de `theme-toggle.js` donde ya se actualizan el
  ícono y el tooltip (una sola función `applyTheme`, sin nuevas fuentes de verdad).
- El ícono sigue siendo la única señal visual que distingue el estado (nunca solo el color), sin cambios respecto a
  `009`.
- El tamaño mínimo de toque (44×44px) y el estilo de foco visible global se conservan exactamente como en `009`.

## Fuera de alcance de este contrato

- Cualquier cambio al mecanismo de `data-theme`, `localStorage` o sincronización entre pestañas: ver
  `specs/009-dark-mode-toggle/contracts/theme-toggle.md`, que sigue vigente para esas secciones.
- El resto de botones de acción del sistema (`.button`, `.button--outline`): no cambian.
