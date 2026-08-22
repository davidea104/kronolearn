# Research: Cambio entre modo claro y modo oscuro

## Contexto técnico existente relevante

- `ui/templates/base.html` es la única plantilla base; las 12 plantillas que actualmente hacen `{% extends
  "base.html" %}` (login, registro, perfil, gestión de roles, catálogo de aprendiz y administración, inscripciones,
  showroom de componentes, home de aprendiz) heredan cualquier cambio hecho ahí. El administrador de Django no
  extiende esta plantilla, por lo que queda naturalmente fuera de alcance sin trabajo adicional.
- El sistema visual **no usa Tailwind CSS ni Alpine.js todavía**: son solo documentación aspiracional en
  `ui/frontend/*.md`. La apariencia real está implementada como CSS puro con custom properties (`--ink`, `--paper`,
  `--border`, etc.) dentro de un único `<style>` en `base.html`, que coincide exactamente con la tabla de tokens de
  `.github/instructions/design.instructions.md`. Solo HTMX está realmente cargado (vía CDN).
- No hay ningún JavaScript propio cargado hoy (`ui/static/js/` no existe aún). Introducir un archivo JS propio para
  esta feature no añade una dependencia nueva (es JS nativo del navegador, no una librería).

## Decisión 1: Mecanismo de aplicación del tema

**Decision**: Usar un atributo `data-theme` en `<html>` (`data-theme="dark"` cuando el modo oscuro está activo;
ausente = modo claro) combinado con un segundo bloque de custom properties CSS bajo el selector
`:root[data-theme="dark"]` que sobreescribe los valores definidos en `:root`.

**Rationale**: Es la extensión mínima del mecanismo ya existente (custom properties + selectores CSS), no requiere
Tailwind ni ninguna librería, y permite que todos los componentes existentes (que ya consumen `var(--ink)`,
`var(--paper)`, etc.) se adapten automáticamente al modo oscuro sin tocar su propio markup ni sus reglas CSS
específicas.

**Alternatives considered**:
- *Clase `.dark` en `<body>`*: equivalente en mecanismo, pero `data-theme` permite expresar exactamente dos estados
  con un solo atributo booleano-como-enum y es más explícito para lectores del código y para pruebas de contrato
  (`assertIn('data-theme="dark"', html)`).
- *`prefers-color-scheme` como única fuente de verdad*: rechazada porque la especificación exige que el modo claro
  sea el valor por defecto para todo usuario nuevo, independientemente de la preferencia del sistema operativo
  (ver Assumptions de `spec.md`).
- *Adoptar Tailwind ahora para su modo `dark:` nativo*: fuera de alcance; introduciría un pipeline de build
  (Node, PostCSS) que hoy no existe en el proyecto, para una feature que no lo necesita.

## Decisión 2: Persistencia y sincronización entre pestañas

**Decision**: Guardar la preferencia en `localStorage` bajo la clave `kronolearn:theme` con valores `"light"` /
`"dark"`. Un script inline síncrono en `<head>` (antes del `<style>`) lee la clave y aplica `data-theme` antes del
primer render, evitando parpadeo (FOUC). Un archivo JS externo (`ui/static/js/theme-toggle.js`, cargado con
`defer`) gestiona el clic del control y escucha el evento nativo `storage` del navegador para reflejar en tiempo
real los cambios hechos en otras pestañas del mismo navegador (el evento `storage` solo se dispara en pestañas
distintas a la que originó el cambio, que es exactamente el comportamiento pedido).

**Rationale**: `localStorage` es síncrono, no requiere red ni cuenta, y el evento `storage` resuelve la
sincronización en tiempo real entre pestañas (FR-009 / SC-005) sin necesidad de `BroadcastChannel`, polling ni
WebSockets — que serían sobreingeniería para un valor de dos estados.

**Alternatives considered**:
- *Cookie de preferencia leída por el servidor*: permitiría fijar `data-theme` en el HTML servido sin script
  inline, pero obligaría a leer y validar la cookie en cada vista (o en un middleware) por un dato que la
  especificación define explícitamente como no autoritativo ni de dominio; se rechaza por añadir superficie de
  servidor a un preferencia puramente de presentación.
- *`BroadcastChannel` API*: cubre el mismo caso de sincronización entre pestañas con una API más moderna, pero
  `storage` ya es suficiente, tiene mejor soporte histórico y no requiere gestionar un canal adicional.
- *Sin sincronización en tiempo real (leer solo al cargar)*: era la recomendación inicial por simplicidad, pero se
  descartó tras la aclaración con el usuario en `/speckit-clarify`, que pidió sincronización en tiempo real.

## Decisión 3: Tokens visuales del modo oscuro

**Decision**: Definir un segundo juego de custom properties invirtiendo fondo/texto y aclarando los acentos para
mantener o mejorar el contraste que ya tienen en modo claro, conservando la misma identidad neo-brutalista (bordes
duros de 2px y sombra dura desplazada, ahora en el color claro en vez de negro):

| Token (modo oscuro) | Valor propuesto | Equivalente en modo claro |
|---|---|---|
| `--paper` | `#121212` | `#FFFFFF` |
| `--ink` | `#F2F2F2` | `#191919` |
| `--ink-secondary` | `#A9B0B9` | `#69727D` |
| `--border` | `#F2F2F2` | `#000000` |
| `--divider` | `#2A2A2A` | `#EEEEEE` |
| `--accent-green` | `#8FD9A8` | `#6EBE87` |
| `--accent-lavender` | `#C9BBFF` | `#B39AFF` |
| `--accent-red` | `#E28C8C` | `#A12B2B` |
| `--shadow-hard` | `6px 6px 0 0 #F2F2F2` | `6px 6px 0 0 #000000` |
| `--shadow-light` | `2px 2px 0 0 #F2F2F2` | `2px 2px 0 0 #000000` |

**Rationale**: Invertir borde y sombra a un tono claro (en vez de mantenerlos negros) es indispensable para que
seguirán siendo visibles sobre un fondo oscuro — un borde negro sobre `#121212` sería casi invisible, rompiendo la
regla de foco/estado visible del sistema de diseño. Los acentos se aclaran respecto a sus equivalentes de modo
claro para que, usados como texto (p. ej. el estado "optimal" de `choice_option.html`), mantengan un contraste
igual o superior al que ya tienen sus equivalentes sobre fondo blanco, cumpliendo FR-007/SC-004 sin necesidad de
igualar un estándar más estricto que el que ya rige el modo claro.

**Alternatives considered**:
- *Fondo negro puro (`#000000`)*: rechazado por fatiga visual y porque el contraste extremo con `#F2F2F2` no
  aporta valor adicional frente a `#121212`, que ya es un estándar común de superficie oscura.
- *Mantener los acentos con el mismo hex en ambos modos*: rechazado porque `--accent-green`/`--accent-lavender`
  usados directamente como color de texto (no solo como fondo/ícono) perderían legibilidad sobre `#121212` si no
  se aclaran.

**Nota de implementación**: estos valores son la propuesta de partida; su verificación final (contraste real,
legibilidad de cada estado de `choice_option.html`, cero uso de blur) se hace visualmente durante la
implementación siguiendo la Sección 10 de `design.instructions.md`, como ya es la práctica establecida del
proyecto para todo componente visual nuevo.

## Decisión 4: Dónde vive el control de cambio de tema

**Decision**: Un nuevo componente reutilizable `templates/ui/components/theme_toggle.html` (un `<button>` real,
sin lógica de negocio, sin acceso a datos), incluido una sola vez en el `<header>` de `ui/templates/base.html`
junto al resto de la navegación. Al vivir en `base.html`, se hereda automáticamente en las 12 plantillas actuales
que lo extienden, sin tocar ninguna de ellas individualmente.

**Rationale**: Coincide con el patrón constitucional (principio 11): componentes nuevos como parciales bajo
`templates/ui/components/`. Colocarlo en `base.html` en vez de en cada plantilla es el único cambio que satisface
FR-005 (disponibilidad consistente en toda la app cubierta) sin editar 12 archivos ni arriesgar divergencia visual
entre páginas.

**Alternatives considered**:
- *Un toggle por página/plantilla*: rechazado por duplicación y riesgo de inconsistencia (viola la regla
  constitucional de reutilización de componentes).

## Resumen de accesibilidad

- El botón es un `<button>` real con texto visible (o texto accesible vía `aria-label`/contenido oculto solo
  visualmente) más un ícono; nunca depende solo del ícono para transmitir su función, cumpliendo la regla de
  "color + indicador" del sistema visual.
- Expone `aria-pressed` reflejando si el modo oscuro está activo, para que lectores de pantalla anuncien el
  estado actual del control tras cada cambio (incluidos los cambios reflejados por sincronización entre pestañas).
- Hereda el estilo de foco visible ya definido globalmente (`:focus-visible { outline: 2px solid var(--border);
  outline-offset: 2px; }`), que en modo oscuro usa el nuevo `--border` claro, manteniéndolo visible sobre el fondo
  oscuro.
- Respeta `prefers-reduced-motion` ya declarado globalmente; la propia transición de tema (si se anima) queda
  cubierta por la regla existente que anula duración de animaciones/transiciones.

## Ítems de Technical Context resueltos

No quedan `NEEDS CLARIFICATION` en el Technical Context del plan: el proyecto ya fija lenguaje (Python 3.14),
framework (Django 5.2.17), y no se introduce ninguna dependencia, servicio de almacenamiento ni plataforma nueva.
