---

description: "Task list template for feature implementation"
---

# Tasks: Cambio entre modo claro y modo oscuro

**Input**: Design documents from `/specs/009-dark-mode-toggle/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/theme-toggle.md, quickstart.md

**Tests**: Esta feature no tiene un mandato constitucional de pruebas (no está en la lista de reglas de dominio del
principio 6), pero se incluyen pruebas de contrato de plantilla siguiendo la convención ya establecida en
`tests/ui/test_base_contract.py`.

**Organization**: Las tareas se agrupan por historia de usuario (spec.md) para permitir implementación y prueba
independientes de cada una.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivo distinto, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1, US2, US3)
- Cada tarea incluye la ruta exacta del archivo

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar `base.html` para poder referenciar el nuevo archivo estático.

- [X] T001 Añadir `{% load static %}` como primera línea de `ui/templates/base.html`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extender la fuente de verdad del sistema visual y el CSS base con el juego de tokens de modo oscuro,
antes de que cualquier historia de usuario pueda considerarse conforme al principio 11 de la constitución.

**⚠️ CRITICAL**: Ninguna historia de usuario puede darse por completa sin esta fase.

- [X] T002 [P] En `.github/instructions/design.instructions.md`: añadir una tabla "Tokens — Modo oscuro" (sección
      1) con los valores de `research.md` → Decisión 3 (`--paper`, `--ink`, `--ink-secondary`, `--border`,
      `--divider`, `--accent-green`, `--accent-lavender`, `--accent-red`, `--shadow-hard`, `--shadow-light`);
      documentar `theme_toggle.html` en el inventario de componentes (sección 4) con su contrato de
      `contracts/theme-toggle.md` (parámetros, `aria-pressed`, `data-theme-toggle`); añadir una fila a la tabla
      "Historial de Cambios" (versión 1.1, fecha de hoy, "Añade modo oscuro y componente theme_toggle").
- [X] T003 En `ui/templates/base.html`: añadir un bloque `:root[data-theme="dark"] { ... }` dentro del `<style>`
      existente, sobreescribiendo `--ink`, `--ink-secondary`, `--paper`, `--border`, `--divider`, `--accent-green`,
      `--accent-lavender`, `--accent-red`, `--shadow-hard`, `--shadow-light` con los valores de T002. No modificar
      ninguna otra regla CSS existente.

**Checkpoint**: El sistema visual admite un tema oscuro completo; ninguna página lo activa todavía.

---

## Phase 3: User Story 1 - Activar el modo oscuro (Priority: P1) 🎯 MVP

**Goal**: Un control visible permite alternar la apariencia de la página actual entre modo claro y modo oscuro.

**Independent Test**: Abrir cualquier página cubierta, hacer clic en el control de tema, y confirmar que la
apariencia cambia de claro a oscuro (y viceversa) sin recargar, conservando todo el contenido y los estados
visuales distinguibles.

### Implementation for User Story 1

- [X] T004 [P] [US1] Crear `templates/ui/components/theme_toggle.html`: un único `<button type="button"
      data-theme-toggle aria-pressed="false">` con ícono + texto accesible (o `.sr-only`), sin lógica de negocio,
      cumpliendo el área mínima de toque de 44×44px, según `contracts/theme-toggle.md`.
- [X] T005 [US1] En `ui/templates/base.html`: incluir `{% include "ui/components/theme_toggle.html" %}` dentro del
      `<nav aria-label="Navegación principal">` del `<header>`, junto al resto de la navegación (depende de T004).
- [X] T006 [P] [US1] Crear `ui/static/js/theme-toggle.js`: al hacer clic en cualquier `[data-theme-toggle]`,
      alternar `document.documentElement.dataset.theme` entre `"dark"` y `"light"`, y actualizar `aria-pressed` en
      todos los `[data-theme-toggle]` de la página. Sin lectura/escritura de `localStorage` todavía (eso es US2).
- [X] T007 [US1] En `ui/templates/base.html` `<head>`: añadir `<script src="{% static 'js/theme-toggle.js' %}"
      defer></script>` después del script de HTMX (depende de T001, T006).
- [X] T008 [P] [US1] En `tests/ui/test_base_contract.py`: añadir pruebas que confirmen que el HTML renderizado de
      `base.html` contiene exactamente un `data-theme-toggle`, el atributo `aria-pressed`, el bloque de CSS
      `:root[data-theme="dark"]` y el `<script>` hacia `theme-toggle.js`.
- [X] T009 [P] [US1] En `templates/ui/components_showroom.html`: añadir una sección "10. Cambio de tema" que
      incluya `theme_toggle.html`, siguiendo el mismo patrón visual (eyebrow + ejemplo) que las 9 secciones
      existentes.

**Checkpoint**: User Story 1 es funcional y probable de forma independiente — el control cambia el tema de la
página actual.

---

## Phase 4: User Story 2 - Conservar la preferencia de tema en el navegador (Priority: P2)

**Goal**: La elección de tema se recuerda en el navegador actual y se propaga en tiempo real entre pestañas.

**Independent Test**: Activar modo oscuro, recargar o navegar a otra página cubierta, y confirmar que sigue en
modo oscuro; abrir una segunda pestaña, cambiar el tema en una, y confirmar que la otra se actualiza sola en menos
de 1 segundo.

### Implementation for User Story 2

- [X] T010 [US2] En `ui/templates/base.html` `<head>`: añadir un `<script>` inline síncrono, colocado antes del
      `<style>` existente, que lea `localStorage.getItem('kronolearn:theme')` (envuelto en `try/catch`, sin
      efecto en caso de error) y, si el valor es `"dark"`, aplique `document.documentElement.dataset.theme =
      "dark"` antes del primer render (evita parpadeo).
- [X] T011 [US2] En `ui/static/js/theme-toggle.js`: al hacer clic, además de alternar `data-theme`, escribir el
      nuevo valor (`"light"` o `"dark"`) en `localStorage.setItem('kronolearn:theme', valor)`, envuelto en
      `try/catch` (depende de T006).
- [X] T012 [US2] En `ui/static/js/theme-toggle.js`: registrar `window.addEventListener('storage', handler)`; si
      `event.key === 'kronolearn:theme'`, aplicar `event.newValue` (o `"light"` si es `null`) como `data-theme` en
      `<html>` y actualizar `aria-pressed` en los `[data-theme-toggle]` de esa pestaña (depende de T006, T011).
- [X] T013 [US2] En `tests/ui/test_base_contract.py`: añadir pruebas que confirmen que el script inline anti-FOUC
      aparece antes del `<style>` y antes del `<script>` de `theme-toggle.js` en el HTML renderizado, y que
      referencia la clave `kronolearn:theme` (depende de T008, T010).

**Checkpoint**: User Stories 1 y 2 funcionan juntas — la preferencia persiste y se sincroniza en tiempo real entre
pestañas del mismo navegador.

---

## Phase 5: User Story 3 - Disponibilidad del control en toda la aplicación (Priority: P3)

**Goal**: Confirmar que el control aparece de forma consistente en login, registro y el área de aprendiz, y que el
administrador de Django permanece sin cambios.

**Independent Test**: Navegar por login, registro y home de aprendiz confirmando presencia y comportamiento
uniforme del control; confirmar que `/admin/` no lo incluye.

### Implementation for User Story 3

- [X] T014 [US3] Crear `tests/ui/test_theme_consistency.py`: pruebas de integración (Django test client) que
      confirmen que las respuestas de `accounts:login`, `accounts:register` y `ui:learner-home` (siguiendo el
      redirect a login si aplica) incluyen `data-theme-toggle`; y que la respuesta de login del admin de Django
      (`/admin/login/`) NO incluye `data-theme-toggle` ni la cadena `kronolearn:theme`.

**Checkpoint**: Las tres historias de usuario son funcionales de forma independiente y en conjunto.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificación final transversal, sin código de producción nuevo.

- [X] T015 [P] Ejecutar `ruff check tests/ui` y `ruff format --check tests/ui` sobre los archivos de prueba
      tocados.
- [X] T016 Ejecutar la revisión visual manual de `quickstart.md` (Sección 10 de
      `.github/instructions/design.instructions.md`) en ambos modos: `/components/`, navegación con teclado,
      login/registro/learner-home, sincronización entre dos pestañas, inspección de sombras/colores sin blur.
- [X] T017 Ejecutar `git diff --name-only` y confirmar que coincide exactamente con la lista cerrada de archivos
      declarada en `plan.md` → Project Structure.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; bloquea todas las historias de usuario.
- **User Story 1 (Phase 3)**: depende de Foundational. Sin dependencia de otras historias.
- **User Story 2 (Phase 4)**: depende de Foundational y de que exista `ui/static/js/theme-toggle.js` (T006 de
      US1), porque extiende el mismo archivo. No es independiente de la implementación de US1, pero sí es
      independientemente probable una vez ambas existen.
- **User Story 3 (Phase 5)**: depende de Foundational y de US1 (el control debe existir en `base.html` para poder
      verificarse en cada página); no depende de US2.
- **Polish (Phase 6)**: depende de que las historias que se vayan a entregar estén completas.

### Parallel Opportunities

- T002 puede ejecutarse en paralelo con T001 (archivos distintos).
- Dentro de US1: T004, T006, T008, T009 pueden ejecutarse en paralelo entre sí (archivos distintos); T005 y T007
  son secuenciales porque ambos editan `ui/templates/base.html` y dependen de T004/T006 respectivamente.
- Dentro de US2: T010, T011, T012, T013 tocan solo 2 archivos ya existentes (`base.html` y `theme-toggle.js`) y
  tienen dependencias directas entre sí; no se recomienda paralelizarlas.
- T015 puede ejecutarse en paralelo con T016/T017.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Completar Phase 1 (Setup) y Phase 2 (Foundational).
2. Completar Phase 3 (User Story 1).
3. **Detener y validar**: el control cambia el tema de la página actual; los estados visuales siguen siendo
   distinguibles; nada de dominio se ve afectado.
4. Esto ya es una demo funcional del "cambio de tema" pedido, aunque sin persistencia todavía.

### Incremental Delivery

1. Setup + Foundational → base lista.
2. + User Story 1 → demo: el toggle cambia el tema en la página actual (MVP técnico).
3. + User Story 2 → demo: el tema persiste y se sincroniza entre pestañas (esto es lo que el usuario pidió
   explícitamente al aceptar la recomendación de persistencia por navegador en `/speckit-clarify`).
4. + User Story 3 → demo: consistencia verificada en login, registro y área de aprendiz; admin confirmado sin
   cambios.
5. Polish → verificación visual manual y de alcance antes de abrir el Pull Request.

## Notes

- No hay tareas de modelos, servicios de dominio, migraciones ni endpoints: esta feature es puramente de
  presentación compartida (ver `data-model.md` y el Constitution Check en `plan.md`).
- Todas las tareas quedan dentro de la lista cerrada de archivos declarada en `plan.md` (principio 16 de la
  constitución); T017 lo verifica explícitamente al final.
