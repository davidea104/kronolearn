# Implementation Plan: Cambio entre modo claro y modo oscuro

**Branch**: `009-dark-mode-toggle` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-dark-mode-toggle/spec.md`

## Summary

Añadir un control global (accesible en toda la app excepto `/admin/`) que permita alternar entre modo claro
(default) y un nuevo modo oscuro, persistiendo la elección solo en el navegador actual (`localStorage`) y
propagándola en tiempo real a otras pestañas abiertas del mismo navegador. El enfoque técnico extiende el
mecanismo de custom properties CSS ya existente en `ui/templates/base.html` con un segundo juego de tokens bajo
`:root[data-theme="dark"]`, sin introducir Tailwind, Alpine.js, ni ningún dato o endpoint en el servidor: es una
feature puramente de presentación compartida, entregada mediante un componente reutilizable
(`templates/ui/components/theme_toggle.html`) y un pequeño script propio (`ui/static/js/theme-toggle.js`).

## Technical Context

**Language/Version**: Python 3.14 (fijado en CI); JavaScript nativo del navegador (sin transpilación ni build)

**Primary Dependencies**: Django 5.2.17 (ya en uso); ninguna dependencia nueva de Python ni de JavaScript

**Storage**: N/A en servidor. `localStorage` del navegador (clave `kronolearn:theme`), documentado en
[data-model.md](data-model.md) y [contracts/theme-toggle.md](contracts/theme-toggle.md)

**Testing**: `python manage.py test` (Django `SimpleTestCase` para contrato de plantillas renderizadas, patrón ya
usado en `tests/ui/test_base_contract.py`); verificación visual manual siguiendo la Sección 10 de
`.github/instructions/design.instructions.md`

**Target Platform**: Navegador web, vía la app Django server-rendered existente

**Project Type**: Web application (monolito modular Django existente); esta feature toca únicamente la capa de
presentación compartida (`ui`)

**Performance Goals**: Cambio de tema perceptible en <2s (SC-001); propagación entre pestañas en <1s (SC-005) —
ambos triviales de cumplir sin red, ya que son una escritura/lectura de `localStorage` y un cambio de atributo CSS

**Constraints**: Sin nuevas dependencias JS; sin cambiar `hx-*`, `name=`, `type=`, `csrf_token` de ningún
formulario existente; sin colores fuera de los tokens definidos; sin sombras con blur; el admin de Django queda
sin tocar

**Scale/Scope**: 12 plantillas actuales que heredan de `base.html` (login, registro, perfil, gestión de roles,
catálogo de aprendiz y administración, inscripciones, showroom de componentes, home de aprendiz); un único punto
de integración (`base.html`) cubre todas automáticamente

No quedan `NEEDS CLARIFICATION` — ver [research.md](research.md) para el detalle de cada decisión.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Evaluación |
|---|---|
| 1. Desarrollo guiado por especificaciones | PASS — spec, clarify y este plan preceden a la implementación. |
| 2. Autoridad del dominio | PASS (no aplica) — no hay regla de negocio; la preferencia de tema no es un valor de dominio y no se deriva en servidor. |
| 3. Contenido administrado como datos | PASS (no aplica) — no se toca contenido de catálogo. |
| 4. Seguridad por defecto | PASS (no aplica) — sin autenticación, sin datos de servidor, sin superficie CSRF nueva (el control no envía formularios). |
| 5. Idempotencia e integridad | PASS (no aplica) — no hay operación que otorgue puntos, progreso ni auditoría. |
| 6. Verificación obligatoria | PASS — el modo oscuro no está en la lista de reglas de dominio con prueba obligatoria; aun así se añaden pruebas de contrato de plantilla siguiendo la convención ya establecida en `tests/ui/`. |
| 7. Main siempre desplegable | PASS — se entrega vía PR y CI, sin commits directos a `main`. |
| 8. Monolito modular | PASS — no se crean apps nuevas; el cambio vive en `ui` y en la plantilla base compartida. |
| 9. Entrega simple e incremental | PASS — no compite con el flujo prioritario del aprendiz; es aditivo y no bloquea ningún paso de inicio de sesión → progreso. |
| 10. Contenido trazable y versionado | PASS (no aplica) — no se publica ni versiona contenido. |
| 11. Frontend server-rendered y accesible | **GATE PRINCIPAL** — requiere que `.github/instructions/design.instructions.md` se amplíe con los tokens de modo oscuro y el nuevo componente `theme_toggle.html` como parte del Phase 1 (ver `research.md` Decisión 3 y `contracts/theme-toggle.md`) antes de que la implementación pueda darse por conforme. El componente se documenta como parcial reutilizable bajo `templates/ui/components/`, sin lógica de negocio ni acceso a datos, cumpliendo foco visible, área de toque de 44px, `prefers-reduced-motion` y la regla de "color + indicador". |
| 12. Autorización en profundidad | PASS (no aplica) — no hay identidad ni permiso involucrado. |
| 13. Privacidad por minimización | PASS — la preferencia nunca viaja al servidor, no se registra en ningún log ni auditoría. |
| 14. Comunicación entre módulos | PASS (no aplica) — no hay señal de dominio ni dependencia entre apps; el único punto de cambio es la plantilla base compartida. |
| 15. Tiempo determinista | PASS (no aplica) — no hay cálculo de día/semana. |
| 16. Propiedad de archivos y migraciones | PASS — lista cerrada de archivos declarada en Project Structure; sin migraciones. |

**Resultado**: PASS con una condición explícita bajo el principio 11, resuelta como parte de los artefactos de
Phase 1 (ver `research.md` y `contracts/theme-toggle.md`); no requiere entrada en Complexity Tracking porque no es
una desviación de la constitución, sino el cumplimiento normal de un requisito que ya exige documentación previa
para componentes nuevos.

## Project Structure

### Documentation (this feature)

```text
specs/009-dark-mode-toggle/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── theme-toggle.md  # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

Lista cerrada de archivos que esta feature puede modificar (principio 16 de la constitución):

```text
.github/instructions/design.instructions.md   # amplía la tabla de tokens con el juego de modo oscuro
                                               # y documenta theme_toggle.html en el inventario de componentes

ui/templates/base.html                        # {% load static %}; script inline anti-FOUC en <head>;
                                               # bloque :root[data-theme="dark"]; incluye theme_toggle.html
                                               # en el <header>; <script defer> a theme-toggle.js

templates/ui/components/
└── theme_toggle.html                         # nuevo componente: botón de cambio de tema (sin lógica de negocio)

templates/ui/components_showroom.html         # añade la sección de muestra del nuevo componente (solo DEBUG)

ui/static/js/
└── theme-toggle.js                           # nuevo: maneja clic, localStorage, evento `storage` entre pestañas

tests/ui/test_base_contract.py                # nuevas aserciones de contrato para data-theme, tokens oscuros
                                               # y presencia del control [data-theme-toggle]
```

Ningún archivo de `accounts/`, `catalog/`, `learning/`, `gamification/`, `analytics/`, `kronolearn/settings/`,
`requirements.in`/`requirements.txt`, ni ninguna migración, se modifica. No hay conflicto de propiedad de
migraciones con otras features en curso porque esta feature no añade ninguna.

**Structure Decision**: Feature contenida en la capa de presentación compartida (`ui` app + plantilla base +
documento de sistema visual). No aplica ninguna de las opciones de estructura multi-proyecto del template: es una
extensión puntual del monolito Django ya existente, sin nuevos servicios, paquetes ni directorios de nivel
superior.

## Complexity Tracking

*Sin violaciones que justificar: el Constitution Check no registra ninguna desviación de la constitución (la
condición del principio 11 se resuelve dentro del flujo normal de Phase 1, no como excepción).*
