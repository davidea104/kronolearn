# Data Model: Control de tema más sutil e integrado

## Alcance del modelo

Sin cambios respecto a `specs/009-dark-mode-toggle/data-model.md`: esta feature no crea, modifica ni consulta
ninguna entidad persistente, no añade migraciones, y no introduce datos nuevos en `localStorage` (sigue usando
exclusivamente la clave `kronolearn:theme` ya existente). Es un cambio de presentación y de mecanismo de nombre
accesible sobre un control ya entregado.

## Concepto ampliado: nombre accesible del control

| Atributo | Antes (009) | Ahora (010) |
|---|---|---|
| Fuente del nombre accesible | Texto visible del `<span data-theme-toggle-label>` | `aria-label` dinámico en el `<button>` |
| Confirmación visible de la acción | Permanente (texto siempre visible junto al ícono) | Solo al enfocar o pasar el mouse (tooltip revelado por CSS) |
| Estado (`aria-pressed`) | Sin cambios | Sin cambios |
| Ícono según modo | Sin cambios (🌙/☀️) | Sin cambios |

No existe ninguna entidad de dominio ni de Python asociada a este concepto; sigue viviendo enteramente en el
navegador (markup + CSS + JavaScript), igual que en `009`.

## Entidades existentes tocadas

Ninguna.
