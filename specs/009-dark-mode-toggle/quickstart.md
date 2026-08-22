# Quickstart: Validación del cambio entre modo claro y modo oscuro

## Prerequisitos

1. Activar el entorno virtual del proyecto e instalar `requirements.txt`.
2. Usar la rama `009-dark-mode-toggle` con las decisiones de
   [research.md](research.md) ya integradas (tokens de modo oscuro, atributo `data-theme`, `localStorage`,
   componente `theme_toggle.html`).
3. Configurar las variables requeridas por `kronolearn.settings.test` (suite rápida) o por
   `kronolearn.settings.development` (para revisión visual en navegador).

## Validación automatizada enfocada

```sh
python manage.py test tests.ui.test_base_contract --settings=kronolearn.settings.test -v 2
python manage.py check --settings=kronolearn.settings.test
ruff check ui/templates tests/ui
ruff format --check ui/templates tests/ui
```

Resultados esperados (ver [contracts/theme-toggle.md](contracts/theme-toggle.md) para el detalle exacto):

- `base.html` renderiza el bloque `:root[data-theme="dark"]` con los tokens de modo oscuro;
- `base.html` renderiza exactamente un control `[data-theme-toggle]` dentro del `<header>`;
- el control expone `aria-pressed` y cumple el área mínima de toque ya cubierta por los estilos globales de
  `button`;
- ninguna plantilla que no extienda `base.html` (en particular, ninguna del admin de Django) se ve afectada.

## Revisión visual manual (obligatoria antes de marcar la feature como completa)

Con el servidor corriendo en modo desarrollo:

```sh
set -a; source .env; set +a
export DJANGO_SETTINGS_MODULE=kronolearn.settings.development
python manage.py runserver
```

Seguir la Sección 10 ("Verificación Visual") de `.github/instructions/design.instructions.md`, ahora también en
modo oscuro:

1. Abrir `/components/` (requiere `DEBUG=True`), activar el modo oscuro y confirmar que los 9+1 componentes
   (incluido el nuevo `theme_toggle`) y todos sus estados (los 5 estados de `choice_option`, los 4 de `alert`,
   etc.) se ven correctamente y ningún estado depende solo del color.
2. Navegar con teclado (Tab, Enter/Espacio) y confirmar foco visible en el control de tema y en el resto de
   elementos interactivos, en ambos modos.
3. Abrir `/accounts/login/`, `/accounts/register/` y `/learn/` (esta última redirige a login si no hay sesión) y
   confirmar que el control de tema está presente y aplica el mismo tema en las tres.
4. Abrir dos pestañas del mismo navegador en cualquiera de esas páginas, cambiar el tema en una, y confirmar que
   la otra se actualiza sola en menos de 1 segundo, sin recargar (SC-005 / FR-009).
5. Recargar la página y confirmar que el tema elegido persiste (SC-003); abrir una ventana de incógnito nueva y
   confirmar que arranca en modo claro (comportamiento por defecto).
6. Inspeccionar el CSS del modo oscuro: sin `filter: blur()`, sombras como `Npx Npx 0 0 <color>` (duras,
   desplazadas, nunca `rgba` con blur), y sin colores fuera de los tokens definidos en `research.md`.
7. Verificar `/admin/`: debe verse exactamente igual que antes de esta feature (sin el control de tema, sin
   `data-theme`).

## Revisión de alcance

```sh
git diff --name-only
```

Para la implementación de la 009 solo deben aparecer (ver Project Structure en `plan.md`):

```text
.github/instructions/design.instructions.md
ui/templates/base.html
templates/ui/components/theme_toggle.html
templates/ui/components_showroom.html
ui/static/js/theme-toggle.js
tests/ui/test_base_contract.py
```

Ningún archivo de `accounts/`, `catalog/`, `learning/`, `gamification/` o `analytics/` (modelos, servicios,
migraciones, vistas) debe aparecer en el diff: esta feature es puramente de presentación compartida.
