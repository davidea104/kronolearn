---
applyTo: "**/templates/**/*.html,**/*.css,tailwind.config.js"
description: Sistema visual de KronoLearn
---

# Sistema Visual de KronoLearn

Neo-brutalismo suave, extraído de diversas fuentes. Este documento es la fuente de verdad para todos los componentes visuales.

## 1. Tokens de Diseño

| Token | Valor | Uso |
|-------|-------|-----|
| **Tipografía** | Work Sans | Todos los textos |
| **Texto principal** | #191919 | Cuerpo, labels, etiquetas |
| **Texto secundario** | #69727D | Helper text, metadatos, muted |
| **Fondo** | #FFFFFF | Blanco puro, sin degradados |
| **Borde** | #000000, 2px | Bordes de cards, inputs, botones |
| **Acento verde** | #6EBE87 | Éxito, logro, completado |
| **Acento lavanda** | #B39AFF | Interactivo, información, hover |
| **Divisor** | #EEEEEE, 1px | Separadores sutiles |
| **Radio** | 10px | Cards, inputs (100px en píldoras) |
| **Sombra** | 6px 6px 0 0 negro | Hard shadow, offset (presión visible) |
| **Sombra leve** | 2px 2px 0 0 negro | Seleccionado, hover (botón presionado) |

## 2. Tipografía Base

```css
font-family: 'Work Sans', sans-serif;
line-height: 1.5;
```

**Escalas:**
- h1, h2: 32–40px, weight 400 (NUNCA bold)
- h3: 20px, weight 400
- body, p: 16px, weight 400
- small, .muted: 14px, weight 400
- eyebrow: 12px, weight 700, uppercase

Énfasis: colorear UNA palabra, no engrosar la frase.

## 3. Reglas Innegociables

1. **Color + indicador:** Ningún estado se distingue SOLO por color. Siempre color + icono/texto/borde.
   - ✓ Borde verde + texto "Completado"
   - ✗ Fondo verde solo

2. **Foco visible:** Todo elemento interactivo (button, a, input, select, textarea, radio, checkbox) SIEMPRE muestra foco:
   ```css
   outline: 2px solid #000000;
   outline-offset: 2px;
   ```

3. **Área de toque:** Mínimo 44px × 44px en todos los elementos interactivos.

4. **Sombras:** SIEMPRE duras y desplazadas. Prohibido blur, prohibido shadow-md/lg/xl.
   - ✓ `6px 6px 0 0 #000000`
   - ✗ `0 4px 6px rgba(0,0,0,0.1)`

5. **Colores:** Solo usar tokens de la tabla. Prohibido:
   - Colores por defecto de Tailwind (text-red-500, bg-gray-100, etc.)
   - Colores arbitrarios fuera del sistema
   - Verde/lavanda como texto sobre blanco (contraste insuficiente)

6. **prefers-reduced-motion:** Respetar en todas las transiciones.

## 4. Inventario de Componentes

### button.html

**Uso:** Botón primario negro o botón secundario con borde.

**Parámetros:**
- `label` (requerido): texto del botón
- `href` (opcional): si está presente, renderiza `<a>` en lugar de `<button>`
- `variant` (opcional): "primary" (default) | "outline"
- `type` (opcional): "submit" | "button" | "reset" (default: "button")
- `class` (opcional): clases adicionales

**Variantes:**
- **primary:** fondo negro, texto blanco, badge circular con flecha en la esquina
- **outline:** fondo blanco, borde negro 2px, texto negro

**Ejemplo:**
```django
{% include "ui/components/button.html" with label="Guardar" type="submit" %}
{% include "ui/components/button.html" with label="Cancelar" variant="outline" href="/tracks" %}
```

---

### eyebrow.html

**Uso:** Píldora negra con texto blanco para rotular secciones.

**Parámetros:**
- `text` (requerido): texto en mayúsculas
- `class` (opcional): clases adicionales

**Regla:** Siempre bold, mayúsculas, pequeño (12px). Ejemplo: "MÓDULO 2 · SESIÓN 3"

**Ejemplo:**
```django
{% include "ui/components/eyebrow.html" with text="MÓDULO 1" %}
```

---

### card.html

**Uso:** Contenedor con borde, fondo blanco, sombra.

**Parámetros:**
- `content` (requerido): contenido HTML interno
- `variant` (opcional): "default" (default) | "raised"
- `class` (opcional): clases adicionales

**Variantes:**
- **default:** borde negro 2px, radio 10px, sombra 6px offset
- **raised:** igual, sombra más pronunciada (8px offset)

**Ejemplo:**
```django
{% include "ui/components/card.html" with content="<h3>Track</h3><p>Descripción</p>" %}
```

---

### choice_option.html

**Uso:** Opción seleccionable (radio button), 5 estados visuales.

**Parámetros:**
- `name` (requerido): atributo name del radio
- `value` (requerido): atributo value
- `label` (requerido): texto visible
- `checked` (opcional): true si está seleccionado
- `state` (opcional): "default" | "selected" | "optimal" | "partial" | "incorrect"

**Markup interno:** Usa `<input type="radio">` real (sr-only) con `<label>` estilizada. Peer-checked para hover/sombra.

**Estados visuales:**
- **default:** borde negro 2px, sombra 6px
- **selected:** borde negro 2px, sombra 2px (efecto botón presionado)
- **optimal:** borde verde #6EBE87 4px left, sombra 2px, texto "✓ Correcto" en verde
- **partial:** borde lavanda #B39AFF 4px left, sombra 2px
- **incorrect:** borde rojo #A12B2B 4px left, sombra 2px, texto tachado

**Ejemplo:**
```django
{% include "ui/components/choice_option.html" with name="answer_1" value="a" label="Opción A" state="optimal" %}
```

---

### progress_bar.html

**Uso:** Barra de progreso con valor numérico.

**Parámetros:**
- `value` (requerido): porcentaje completado (0–100)
- `label` (opcional): etiqueta descriptiva
- `class` (opcional): clases adicionales

**Visual:** Barra con fondo #EEEEEE, relleno en verde #6EBE87, y porcentaje en texto (ej: "65%") a la derecha.

**Ejemplo:**
```django
{% include "ui/components/progress_bar.html" with value=65 label="Progreso" %}
```

---

### stat.html

**Uso:** Cifra grande + etiqueta (para dashboards).

**Parámetros:**
- `number` (requerido): número a mostrar
- `label` (requerido): descripción de la métrica
- `accent` (opcional): "green" | "lavender" | "default"
- `class` (opcional): clases adicionales

**Visual:** Número en 48px weight 400, etiqueta en 14px gris, opcional color acento en número.

**Ejemplo:**
```django
{% include "ui/components/stat.html" with number=42 label="Módulos completados" accent="green" %}
```

---

### step_number.html

**Uso:** Numeración de pasos (01, 02, 03) con etiqueta.

**Parámetros:**
- `number` (requerido): número de paso (1–9, renderiza con padding: 01, 02, etc.)
- `label` (requerido): etiqueta del paso
- `class` (opcional): clases adicionales

**Visual:** Número en 32px gris #69727D, label a su derecha.

**Ejemplo:**
```django
{% include "ui/components/step_number.html" with number=1 label="Registra tu perfil" %}
```

---

### empty_state.html

**Uso:** Placeholder centrado cuando no hay contenido.

**Parámetros:**
- `icon` (opcional): emoji o HTML de icono
- `headline` (requerido): título (ej: "No hay módulos")
- `message` (opcional): texto descriptivo
- `action_label` (opcional): texto del botón de acción
- `action_href` (opcional): destino del botón
- `class` (opcional): clases adicionales

**Visual:** Centrado, icon (si existe) arriba, headline en h3, message en body, botón abajo.

**Ejemplo:**
```django
{% include "ui/components/empty_state.html" with icon="📚" headline="Sin contenido" message="Crea tu primer track." action_label="Nuevo track" action_href="/tracks/new" %}
```

---

### alert.html

**Uso:** Notificación con borde de color y texto.

**Parámetros:**
- `message` (requerido): texto del alert
- `type` (requerido): "success" | "error" | "info" | "warning"
- `class` (opcional): clases adicionales

**Variantes de borde (left border 4px):**
- **success:** #6EBE87 (verde)
- **error:** #A12B2B (rojo)
- **info:** #B39AFF (lavanda)
- **warning:** #F59E0B (ámbar)

**Visual:** Borde izquierdo de color, fondo blanco, texto #191919, padding interno.

**Ejemplo:**
```django
{% include "ui/components/alert.html" with message="Cambios guardados" type="success" %}
```

---

## 5. Reglas de Layout (Markup sin componentes)

- **Spacing:** Usa múltiplos de 4px o 8px (px-4, py-8, gap-4, etc. en valores real, no clases Tailwind).
- **Grid:** Usa `display: grid; gap: 1rem;` para listas de cards.
- **Flexbox:** Para layouts simples (header, footer, nav).
- **Bloques de contenido:** max-width 56rem (896px) para legibilidad.

## 6. Reglas de HTMX

- NO cambies atributos `hx-*`: ni URL, ni target, ni swap. Solo envuelve el markup.
- `hx-target` DEBE seguir siendo válido después de envolver.
- `hx-swap="innerHTML"` reemplaza contenido dentro del selector: verifica que el selector siga apuntando al lugar correcto.
- Ejemplo: Si tienes `<table id="module-rows">`, puedes estilizar el `<table>` pero NO mover ni renombrar el id.

## 7. Reglas de Formularios

- Preserva TODOS los atributos: `name=`, `type=`, `value=`, `{% csrf_token %}`.
- Estructura permitida: envuelve `<label>` + `<input>` + `<error>` en un div, añade clases de estilo.
- NO uses `<fieldset>` ni `<legend>` para cambiar semántica.
- Errors: mostrar inline bajo el input, en texto rojo #A12B2B.
- Radio/checkbox: usar `<input type="radio">` / `<input type="checkbox">` reales con `<label>` contigua.

## 8. Prohibiciones Explícitas

- ✗ No cambies nombre de plantillas ni las muevas a otras carpetas.
- ✗ No cambies la estructura de bloques en base.html.
- ✗ No cambies ningún atributo hx-*.
- ✗ No cambies name=, type= de inputs, ni csrf_token.
- ✗ No añadas dependencias JavaScript (solo HTMX, Alpine, Tailwind, que ya están).
- ✗ No toques migraciones ni settings.
- ✗ No uses estilos inline (style=) salvo en casos excepcionales (ej: background-image).
- ✗ No uses blur en sombras.
- ✗ No uses colores fuera del sistema de tokens.
- ✗ No copies contenido HTML de componentes en este archivo: son la fuente de verdad en sus archivos.

---

## 9. Referencia de Componentes

Para incluir un componente en una plantilla:

```django
{% load static %}
{# ... #}

{# Botón primario #}
{% include "ui/components/button.html" with label="Continuar" type="submit" %}

{# Card con contenido #}
{% include "ui/components/card.html" with content="<h3>Bienvenida</h3>" %}

{# Alert de éxito #}
{% include "ui/components/alert.html" with message="Guardado con éxito" type="success" %}
```

Cada componente es un archivo independiente bajo `templates/ui/components/` y recibe sus datos por `{% include ... with ... %}`. Ninguno consulta la BD ni contiene lógica de negocio.

---

## 10. Verificación Visual

Antes de marcar un trabajo como completo:

1. **Abre la página de componentes** (solo DEBUG=True): `/components/`
   - Todos los 9 componentes visibles
   - Todos los estados visible (choice_option con 5 estados, etc.)
   - Ningún estado depende solo de color

2. **Navega con teclado:**
   - Tab: foco visible en TODOS los botones, inputs, links
   - Enter/Space: activa acciones
   - Arrow keys: no necesarias para base, pero radio/checkbox debe funcionar

3. **Inspecciona CSS:**
   - Sin `filter: blur()`
   - Sin colores fuera de la tabla de tokens
   - Sombras como `6px 6px 0 0` (hard, offset, NO blur)

4. **Pantalla ampliada + zoom 200%:**
   - Elementos interactivos siguen siendo 44px×44px mínimo
   - Texto legible
   - Layouts no se rompen

---

## Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-08-21 | Creación: sistema visual neo-brutalista con 9 componentes |
