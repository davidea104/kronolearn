# Quickstart: Validación del control de tema más sutil

## Prerequisitos

1. Activar el entorno virtual del proyecto e instalar `requirements.txt`.
2. `specs/009-dark-mode-toggle` debe estar ya implementada (el control, el mecanismo `data-theme`, la persistencia
   y la sincronización entre pestañas siguen vigentes y no se tocan aquí).
3. Usar la rama `010-subtle-theme-toggle` con las decisiones de [research.md](research.md) integradas.

## Validación automatizada enfocada

```sh
python manage.py test tests.ui.test_base_contract tests.ui.test_theme_consistency --settings=kronolearn.settings.test -v 2
python manage.py check --settings=kronolearn.settings.test
ruff check tests/ui
ruff format --check tests/ui
```

Resultados esperados (ver [contracts/theme-toggle-style.md](contracts/theme-toggle-style.md)):

- el control renderizado ya no lleva las clases `.button`/`.button--outline`;
- el `<button>` expone un `aria-label` dinámico además de `aria-pressed`;
- `tests.ui.test_theme_consistency` sigue pasando sin cambios (el control sigue presente en login, registro,
  learner-home, y ausente en `/admin/`) — esta feature no cambia esa cobertura, solo su presentación.

## Revisión visual manual (obligatoria antes de marcar la feature como completa)

Con el servidor corriendo en modo desarrollo, seguir la Sección 10 de
`.github/instructions/design.instructions.md`, enfocada en el control de tema:

1. Abrir cualquier página cubierta y confirmar que el control **no** se ve como un botón con caja: sin borde
   visible, sin sombra dura, en reposo.
2. Pasar el mouse sobre el control y confirmar que aparece una etiqueta legible indicando la acción ("Modo
   oscuro"/"Modo claro" según corresponda), y que desaparece al quitar el mouse.
3. Navegar con Tab hasta el control y confirmar que también aparece la misma etiqueta al recibir el foco (no solo
   con el mouse), y que el foco sigue siendo visible (outline de 2px).
4. Con un lector de pantalla (o inspeccionando el árbol de accesibilidad del navegador), confirmar que el nombre
   anunciado al enfocar el control coincide con la acción disponible, y que cambia tras activarlo.
5. Confirmar en zoom 200% que el área de toque del control sigue siendo de al menos 44×44px.
6. Repetir 1–5 en modo oscuro activo (el control debe seguir siendo igual de sutil, con el tooltip legible sobre
   fondo oscuro).
7. Confirmar que ningún otro botón de la aplicación ("Guardar", "Cerrar sesión", etc.) cambió de apariencia.

## Revisión de alcance

```sh
git diff --name-only
```

Para la implementación de la 010 solo deben aparecer:

```text
.github/instructions/design.instructions.md
templates/ui/components/theme_toggle.html
templates/ui/components_showroom.html
ui/templates/base.html
ui/static/js/theme-toggle.js
tests/ui/test_base_contract.py
```

Ningún archivo de `accounts/`, `catalog/`, `learning/`, `gamification/`, `analytics/`, ni ningún otro componente de
`templates/ui/components/`, debe aparecer en el diff: esta feature toca únicamente el control de tema ya existente.
