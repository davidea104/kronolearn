# Data Model: Cambio entre modo claro y modo oscuro

## Alcance del modelo

La feature no crea, modifica ni consulta ninguna entidad persistente. No añade campos al modelo `Account` ni a
ningún otro modelo de Django, no añade migraciones, y no introduce ninguna tabla ni caché de servidor. El único
"dato" de la feature vive exclusivamente en el navegador del usuario, tal como lo define la especificación
(`spec.md` → Key Entities y Assumptions).

## Preferencia de tema (concepto, no persistente en servidor)

| Atributo | Valor | Notas |
|---|---|---|
| Almacenamiento | `localStorage`, clave `kronolearn:theme` | Ver [contracts/theme-toggle.md](contracts/theme-toggle.md) |
| Valores posibles | `"light"` \| `"dark"` | Ausencia de la clave equivale a `"light"` |
| Alcance | Por navegador/dispositivo | No se asocia a `Account`; no se sincroniza entre dispositivos (decisión de alcance registrada en `spec.md`) |
| Reflejo en el documento | Atributo `data-theme` en `<html>` | `data-theme="dark"` cuando el modo oscuro está activo; ausente en modo claro |
| Propagación entre pestañas | Evento nativo `storage` del navegador | Ver Decisión 2 en `research.md` |

No existe una representación de esta preferencia en Python/Django: ninguna vista, formulario, servicio o modelo la
lee, la escribe o la valida. Esto es intencional y se deriva directamente de la Autoridad del dominio (principio 2
de la constitución): esta feature no es una regla de negocio, es una preferencia de presentación.

## Entidades existentes tocadas

Ninguna. No se modifica `Account`, `Track`, `Module`, `Enrollment`, ni ningún otro modelo de `accounts`, `catalog`,
`learning`, `gamification` o `analytics`.
