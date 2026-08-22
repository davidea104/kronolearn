# UI Contract: Control de cambio de tema (claro/oscuro)

## Componente

- **Archivo**: `templates/ui/components/theme_toggle.html`
- **Parámetros**: ninguno (no recibe `include ... with`; su estado inicial lo determina el propio `<html
  data-theme="...">` ya renderizado, no una variable de contexto de Django)
- **Markup**: un único `<button type="button" data-theme-toggle aria-pressed="...">`, sin lógica de negocio, sin
  acceso a la base de datos, conforme al principio 11 de la constitución.
- **Inclusión**: una sola vez, en el `<header>` de `ui/templates/base.html`, junto al resto de la navegación. Se
  hereda automáticamente en toda plantilla que haga `{% extends "base.html" %}`.

No se añade ningún endpoint HTTP, vista, formulario, ni variante HTMX. El control no envía ninguna solicitud al
servidor en ningún momento de su ciclo de vida.

## Contrato del atributo `data-theme`

| Estado | Atributo en `<html>` |
|---|---|
| Modo claro (por defecto) | Sin atributo `data-theme`, o `data-theme="light"` |
| Modo oscuro | `data-theme="dark"` |

El CSS existente en `:root { ... }` define los valores de modo claro; un bloque nuevo
`:root[data-theme="dark"] { ... }` sobreescribe únicamente las custom properties listadas en
[../research.md](../research.md#decisión-3-tokens-visuales-del-modo-oscuro). Ningún otro selector CSS debe
depender de `data-theme`; los componentes existentes siguen consumiendo `var(--ink)`, `var(--paper)`, etc. sin
cambios en su propio markup o reglas.

## Contrato de almacenamiento (`localStorage`)

| Clave | Valores | Escritor | Lector |
|---|---|---|---|
| `kronolearn:theme` | `"light"` \| `"dark"` | `ui/static/js/theme-toggle.js`, al hacer clic en el control | Script inline en `<head>` (aplica antes del primer render) y `theme-toggle.js` (aplica en clic y en el evento `storage`) |

Ninguna solicitud HTTP lee ni escribe esta clave; vive exclusivamente en el navegador. Un fallo al acceder a
`localStorage` (por ejemplo, almacenamiento bloqueado) DEBE tratarse silenciosamente como modo claro, sin lanzar
errores visibles ni romper el render de la página.

## Contrato de sincronización entre pestañas

`theme-toggle.js` escucha el evento nativo `window.addEventListener('storage', handler)`. Cuando el evento reporta
un cambio en la clave `kronolearn:theme` (`event.key === 'kronolearn:theme'`), el handler:

1. Aplica `event.newValue` (o `"light"` si es `null`) como `data-theme` en `<html>` de esa pestaña.
2. Actualiza `aria-pressed` en cualquier `[data-theme-toggle]` presente en esa pestaña para reflejar el nuevo
   estado.

Este evento nunca se dispara en la pestaña que originó el cambio (comportamiento nativo del navegador), por lo que
esa pestaña actualiza su propio estado directamente en el manejador de clic, no a través de este evento.

## Contrato de accesibilidad

- El control es un `<button>` real (operable con teclado por defecto, sin `tabindex` artificial).
- Expone `aria-pressed="true"` cuando el modo oscuro está activo, `aria-pressed="false"` en modo claro.
- Incluye un texto accesible (visible o mediante contenido con clase `.sr-only` ya definida en `base.html`) que
  indique la acción, además de cualquier ícono; nunca depende solo del ícono o del color.
- Cumple el área mínima de toque de 44×44px ya exigida por el sistema visual.
- Hereda el estilo de foco visible global (`:focus-visible`), que en modo oscuro usa el `--border` claro definido
  para ese modo.

## Fuera de alcance de este contrato

- El administrador de Django (`/admin/`): no incluye este componente ni el script asociado.
- Cualquier persistencia en servidor, por cuenta, o entre dispositivos: explícitamente fuera de alcance según la
  decisión registrada en `spec.md`.
