# Data Model: Exploración e inscripción en tracks

Esta feature no añade modelos ni migraciones. Reutiliza las entidades persistidas por la feature 004 y las proyecciones ya publicadas por `catalog`.

## Entidades reutilizadas (sin cambios de esquema)

### `learning.Enrollment`

| Campo | Tipo | Regla relevante para esta feature |
| --- | --- | --- |
| `id` | UUID | Clave primaria existente, sin cambios |
| `account` | FK a `accounts.Account` | Identidad tomada de `request.user`; nunca de un formulario o URL |
| `track` | FK a `catalog.Track` | Debe corresponder a un track resuelto por `get_active_track` |
| `enrolled_at` | Datetime | Sin cambios; ordena `list_enrollments` |
| `status` | `ACTIVE`/`WITHDRAWN` | Esta feature solo crea filas en `ACTIVE`; el retiro de una inscripción está fuera de alcance |

**Restricción autoritativa reutilizada**: `learning_enrollment_account_track_unique` (única por `account`+`track`). `enroll` depende de esta restricción para su idempotencia; no se añade ninguna comprobación de aplicación que la sustituya.

### `catalog.Track` (proyección de solo lectura)

Leído exclusivamente a través de `catalog.services.queries.list_active_tracks()` y `get_active_track(track_id)`. Esta feature consume los campos ya proyectados por esos servicios (`id`, `title`, `description`, `audience`, `position`) y, para el conteo de módulos, la lista `active_modules` que `get_active_track` adjunta por `Prefetch`. Ningún campo ni regla de `Track` se redefine aquí.

## Modelo de presentación (no persistido)

Cada tarjeta de track en el listado y en el detalle se arma con esta forma efímera, calculada en la vista a partir de los servicios existentes y nunca almacenada:

| Campo | Origen |
| --- | --- |
| `track` | `catalog.services.queries.list_active_tracks()` / `get_active_track()` |
| `module_count` | `len(get_active_track(track.id).active_modules)` |
| `is_enrolled` | `learning.services.enrollment.get_enrollment(request.user, track) is not None` |

Esta forma no es un modelo de Django; documenta el contrato de contexto de plantilla usado por `list.html`, `detail.html` y `partials/track_card.html`.

## Transiciones relevantes

`Enrollment` no gana nuevas transiciones. La única escritura de esta feature es la creación de una fila `ACTIVE` la primera vez que una cuenta se inscribe en un track; los envíos posteriores para el mismo par cuenta-track no producen una transición nueva, solo devuelven la fila existente.
