---

description: "Task list template for feature implementation"
---

# Tasks: Control de tema más sutil e integrado

**Input**: Design documents from `/specs/010-subtle-theme-toggle/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/theme-toggle-style.md, quickstart.md

**Tests**: Sin mandato constitucional (no está en la lista de reglas de dominio del principio 6); se extiende
`tests/ui/test_base_contract.py` siguiendo la convención ya establecida en `009-dark-mode-toggle`.

**Organization**: Las tareas se agrupan por historia de usuario de `spec.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivo distinto, sin dependencias pendientes)
- **[Story]**: US1, US2, US3

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Actualizar la fuente de verdad del sistema visual antes de restilizar el componente, conforme al
principio 11 de la constitución.

- [X] T001 [P] En `.github/instructions/design.instructions.md`: reescribir la entrada de `theme_toggle.html`
      (sección 4) con el nuevo markup, tratamiento visual "sin caja" y contrato de accesibilidad de
      `contracts/theme-toggle-style.md`; añadir fila a "Historial de Cambios" (versión 1.2, fecha de hoy, "El
      control de tema pasa a ser solo ícono, sin borde ni sombra, con aria-label y tooltip revelado al enfocar/
      pasar el mouse").

**Checkpoint**: La documentación del sistema visual ya describe el nuevo contrato; el componente aún no se ha
tocado.

---

## Phase 2: User Story 1 - Percibir el control como parte natural de la navegación (Priority: P1) 🎯 MVP

**Goal**: El control se ve como un ícono sin borde ni sombra en reposo, y revela una confirmación textual al
enfocarlo o pasar el mouse.

**Independent Test**: Comparar visualmente el control contra un botón de acción existente (por ejemplo "Cerrar
sesión" o "Guardar"): no debe tener el borde ni la sombra dura que sí tienen esos botones; al pasar el mouse o
enfocarlo con teclado, debe aparecer un texto confirmando su acción.

### Implementation for User Story 1

- [X] T002 [P] [US1] En `templates/ui/components/theme_toggle.html`: quitar las clases `.button`/`.button--outline`
      dejando solo `class="theme-toggle"`; envolver el ícono en `<span class="theme-toggle__icon" ...>`; convertir
      el `<span data-theme-toggle-label>` en `<span class="theme-toggle__tooltip" aria-hidden="true"
      data-theme-toggle-label>`, según `contracts/theme-toggle-style.md`.
- [X] T003 [P] [US1] En `ui/templates/base.html` (`<style>` existente): añadir las reglas `.theme-toggle` (sin
      borde, sin sombra, fondo transparente, conserva `min-height`/`min-width: 44px`, fondo `var(--divider)` en
      `:hover`), `.theme-toggle__icon` y `.theme-toggle__tooltip` (oculto en reposo, revelado por CSS puro en
      `:hover`/`:focus-visible`, estilo tipo `.eyebrow`), según `research.md` → Decisiones 1, 3 y 4.
- [X] T004 [P] [US1] En `templates/ui/components_showroom.html`: ajustar el texto de apoyo de la sección "10.
      Cambio de tema" para indicar que la etiqueta ahora aparece solo al enfocar o pasar el mouse.
- [X] T005 [P] [US1] En `tests/ui/test_base_contract.py`: añadir aserciones que confirmen que el HTML renderizado
      del control NO contiene `class="button` ni `button--outline`, y sí contiene `theme-toggle__tooltip`.

**Checkpoint**: El control ya no se ve como un botón de acción; el tooltip se revela correctamente por CSS.

---

## Phase 3: User Story 2 - Mantener la identificación con tecnología de asistencia (Priority: P2)

**Goal**: El nombre accesible del control vive en un `aria-label` dinámico, siempre presente, coherente con el
modo vigente.

**Independent Test**: Inspeccionar el nombre accesible del control (por ejemplo, con las herramientas de
accesibilidad del navegador o un lector de pantalla) antes y después de activarlo, y confirmar que describe
correctamente la acción disponible en cada momento.

### Implementation for User Story 2

- [X] T006 [US2] En `templates/ui/components/theme_toggle.html`: añadir `aria-label="Cambiar a modo oscuro"` como
      valor inicial del `<button>` (coherente con el modo claro por defecto) (depende de T002, mismo archivo).
- [X] T007 [P] [US2] En `ui/static/js/theme-toggle.js`: extender `applyTheme` para calcular una sola vez el texto
      de la acción ("Cambiar a modo oscuro"/"Cambiar a modo claro") y usarlo tanto para
      `button.setAttribute('aria-label', ...)` como para el `textContent` del `[data-theme-toggle-label]`.
- [X] T008 [US2] En `tests/ui/test_base_contract.py`: añadir una aserción que confirme que el HTML renderizado
      inicial incluye `aria-label="Cambiar a modo oscuro"` (depende de T005, mismo archivo).

**Checkpoint**: El nombre accesible es correcto y único; no depende del contenido visible del tooltip.

---

## Phase 4: User Story 3 - No perder ninguna garantía ya lograda (Priority: P3)

**Goal**: Confirmar que el mecanismo funcional y de accesibilidad entregado en `009-dark-mode-toggle` sigue intacto.

**Independent Test**: Repetir las pruebas de tamaño de toque, foco visible, persistencia y sincronización entre
pestañas ya definidas para el control, y confirmar que siguen cumpliéndose sin cambios.

### Implementation for User Story 3

- [X] T009 [US3] Ejecutar `python manage.py test tests.ui --settings=kronolearn.settings.test` y confirmar 0
      fallos, verificando en particular que `tests/ui/test_theme_consistency.py` y las aserciones ya existentes de
      `tests/ui/test_base_contract.py` sobre `:root[data-theme="dark"]`, el script `theme-toggle.js` y
      `aria-pressed` siguen pasando sin haberlas modificado más allá de lo hecho en US1/US2 (depende de T001–T008).

**Checkpoint**: Las tres historias de usuario funcionan de forma independiente y en conjunto; nada de `009` se
rompió.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T010 [P] Ejecutar `ruff check tests/ui` y `ruff format --check tests/ui`.
- [X] T011 Ejecutar la revisión visual manual de `quickstart.md`: sin caja en reposo, tooltip revelado en
      hover/focus, foco visible, área de toque de 44×44px en zoom 200%, en ambos modos, y confirmar que ningún
      otro botón de la aplicación cambió de apariencia.
- [X] T012 Ejecutar `git diff --name-only` y confirmar que coincide exactamente con la lista cerrada de archivos
      declarada en `plan.md` → Project Structure.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: sin dependencias; bloquea todas las historias de usuario.
- **User Story 1 (Phase 2)**: depende de Foundational. Sin dependencia de otras historias.
- **User Story 2 (Phase 3)**: depende de Foundational y de que exista `theme_toggle.html` restilizado (T002 de
      US1), porque añade un atributo al mismo elemento. No depende del resto de US1.
- **User Story 3 (Phase 4)**: depende de que US1 y US2 estén completas (es una verificación de no regresión sobre
      ambas).
- **Polish (Phase 5)**: depende de que todas las historias estén completas.

### Parallel Opportunities

- T002, T003, T004, T005 (todos dentro de US1) pueden ejecutarse en paralelo: son archivos distintos y el
      contrato de nombres de clases ya está fijado en `contracts/theme-toggle-style.md`.
- T007 (US2) puede ejecutarse en paralelo con T006/T008 (archivo distinto).
- T010 puede ejecutarse en paralelo con T011/T012.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Completar Phase 1 (Foundational).
2. Completar Phase 2 (User Story 1).
3. **Detener y validar**: el control ya no se ve como un botón de acción; el tooltip funciona con mouse y
      teclado. Esto ya cumple el pedido original del usuario ("más sutil e integrado").

### Incremental Delivery

1. Foundational → documentación del sistema visual actualizada.
2. + User Story 1 → demo: control sin caja, tooltip revelado en hover/focus (MVP visual).
3. + User Story 2 → demo: nombre accesible correcto y verificable con tecnología de asistencia.
4. + User Story 3 → confirmación explícita de que nada de `009` se rompió.
5. Polish → verificación visual manual y de alcance antes de abrir el Pull Request.

## Notes

- No hay tareas de modelos, servicios de dominio, migraciones ni endpoints: esta feature es puramente de
  presentación sobre un componente ya existente (ver `data-model.md` y el Constitution Check en `plan.md`).
- Ningún archivo nuevo se crea; todos los archivos tocados ya existían antes de esta feature.
