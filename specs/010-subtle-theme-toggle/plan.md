# Implementation Plan: Control de tema más sutil e integrado

**Branch**: `010-subtle-theme-toggle` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-subtle-theme-toggle/spec.md`

## Summary

Restilizar el control de cambio de tema entregado en `009-dark-mode-toggle` para que deje de verse como un botón
de acción (borde 2px + sombra dura + fondo sólido) y pase a ser un ícono sin caja, integrado visualmente en la
navegación. El nombre accesible permanente se mueve a un `aria-label` dinámico en el propio `<button>`; la
confirmación textual de la acción se revela solo al enfocar o pasar el mouse, mediante un tooltip mostrado con CSS
puro (sin JavaScript adicional para su visibilidad). El mecanismo funcional (`data-theme`, `localStorage`,
sincronización entre pestañas) no cambia: esta es una feature puramente de presentación sobre un componente ya
existente.

## Technical Context

**Language/Version**: Python 3.14 (sin cambios); JavaScript nativo del navegador (sin cambios)

**Primary Dependencies**: Django 5.2.17 (sin cambios); ninguna dependencia nueva

**Storage**: N/A — sin cambios respecto a `009` (`localStorage`, clave `kronolearn:theme`)

**Testing**: `python manage.py test` (extensión de `tests/ui/test_base_contract.py`); verificación visual manual
siguiendo la Sección 10 de `.github/instructions/design.instructions.md`

**Target Platform**: Navegador web, vía la app Django server-rendered existente

**Project Type**: Web application (monolito modular Django existente); esta feature toca únicamente un componente
de presentación ya entregado

**Performance Goals**: Sin objetivos nuevos; el tooltip se revela mediante CSS puro (`:hover`/`:focus-visible`),
sin coste de JavaScript adicional en la interacción

**Constraints**: No debe cambiar el mecanismo funcional de `009` (default claro, persistencia, sincronización entre
pestañas); no debe alterar ningún otro botón o componente existente; debe conservar el área mínima de toque de
44×44px y el estilo de foco visible global ya exigidos

**Scale/Scope**: Un único componente (`templates/ui/components/theme_toggle.html`) y su CSS/JS de soporte en
`ui/templates/base.html` / `ui/static/js/theme-toggle.js`; sin cambios en el número de páginas cubiertas (las
mismas de `009`, todas excepto `/admin/`)

No quedan `NEEDS CLARIFICATION` — ver [research.md](research.md).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Evaluación |
|---|---|
| 1. Desarrollo guiado por especificaciones | PASS — spec, clarify (sin ambigüedades adicionales) y este plan preceden a la implementación. |
| 2. Autoridad del dominio | PASS (no aplica) — sigue sin haber regla de negocio ni dato de dominio involucrado. |
| 3. Contenido administrado como datos | PASS (no aplica). |
| 4. Seguridad por defecto | PASS (no aplica) — sin cambios de superficie de seguridad. |
| 5. Idempotencia e integridad | PASS (no aplica). |
| 6. Verificación obligatoria | PASS — se extiende `tests/ui/test_base_contract.py` con aserciones sobre el nuevo markup/`aria-label`, siguiendo la convención ya establecida; no es una regla de dominio con prueba constitucionalmente obligatoria. |
| 7. Main siempre desplegable | PASS — vía PR y CI. |
| 8. Monolito modular | PASS — no se crean apps ni archivos nuevos de infraestructura. |
| 9. Entrega simple e incremental | PASS — es un refinamiento visual aislado, no bloquea el flujo prioritario del aprendiz. |
| 10. Contenido trazable y versionado | PASS (no aplica). |
| 11. Frontend server-rendered y accesible | **GATE PRINCIPAL** — requiere actualizar la entrada de `theme_toggle.html` en `.github/instructions/design.instructions.md` (markup, contrato de accesibilidad y tratamiento visual) como parte de Phase 1, y verificar visualmente que se conservan foco visible, área de toque de 44px, `prefers-reduced-motion` (heredado de la regla global) y la regla de "nunca depender solo del color" (el ícono sigue siendo el indicador de estado). |
| 12. Autorización en profundidad | PASS (no aplica). |
| 13. Privacidad por minimización | PASS (no aplica) — sin cambios; la preferencia sigue sin viajar al servidor. |
| 14. Comunicación entre módulos | PASS (no aplica). |
| 15. Tiempo determinista | PASS (no aplica). |
| 16. Propiedad de archivos y migraciones | PASS — lista cerrada de archivos declarada abajo; sin migraciones; todos los archivos ya existían (ninguno nuevo). |

**Resultado**: PASS con la misma condición estructural que en `009` bajo el principio 11 (actualizar la
documentación del sistema visual como parte del propio cambio), resuelta en Phase 1. No requiere entrada en
Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/010-subtle-theme-toggle/
├── plan.md                      # This file (/speckit-plan command output)
├── research.md                  # Phase 0 output (/speckit-plan command)
├── data-model.md                # Phase 1 output (/speckit-plan command)
├── quickstart.md                # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── theme-toggle-style.md    # Phase 1 output (/speckit-plan command)
└── tasks.md                     # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

Lista cerrada de archivos que esta feature puede modificar (principio 16 de la constitución) — todos ya existen,
ninguno se crea:

```text
.github/instructions/design.instructions.md   # actualiza la entrada de theme_toggle.html (markup, contrato de
                                               # accesibilidad, tratamiento visual sin caja) y el Historial de Cambios

templates/ui/components/theme_toggle.html     # restilizado: sin clases .button/.button--outline, añade aria-label,
                                               # el span de texto pasa a ser un tooltip aria-hidden

templates/ui/components_showroom.html         # ajusta, si hace falta, el texto de apoyo de la sección 10

ui/templates/base.html                        # nuevas reglas CSS .theme-toggle / .theme-toggle__icon /
                                               # .theme-toggle__tooltip en el <style> existente; sin cambios
                                               # estructurales al <head> ni a la inclusión del componente

ui/static/js/theme-toggle.js                  # applyTheme también actualiza aria-label y el texto del tooltip

tests/ui/test_base_contract.py                # nuevas aserciones: ausencia de clases .button/.button--outline en
                                               # el control, presencia de aria-label dinámico
```

Ningún archivo de `accounts/`, `catalog/`, `learning/`, `gamification/`, `analytics/`, `kronolearn/settings/`, ni
ningún otro componente bajo `templates/ui/components/`, se modifica. No hay migraciones ni conflicto de propiedad
de migraciones.

**Structure Decision**: Mismo patrón que `009`: cambio contenido en la capa de presentación compartida, sin nuevas
apps, paquetes ni directorios. A diferencia de `009`, no se crea ningún archivo nuevo — todos los archivos tocados
ya existían.

## Complexity Tracking

*Sin violaciones que justificar.*
