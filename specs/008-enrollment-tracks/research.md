# Research: Exploración e inscripción en tracks

## Reutilización de la consulta de tracks activos

**Decision**: El listado y el detalle de inscripción invocan `catalog.services.queries.list_active_tracks()` y `catalog.services.queries.get_active_track(track_id)` como única fuente de verdad sobre qué track está disponible. Ningún código de `learning` importa `catalog.models` ni reimplementa el filtro `status=ACTIVE`.

**Rationale**: El principio 14 de la constitución prohíbe que un módulo dependa de los modelos de otra app para lecturas; exige servicios de consulta publicados. `catalog.services.queries` ya expone exactamente esas dos funciones, cableadas desde la feature 004 y usadas por las vistas de aprendiz existentes en `catalog`.

**Alternatives considered**: Reimplementar el filtro de estado activo dentro de `learning` fue descartado porque duplicaría una regla de dominio ajena y violaría el principio 14. Importar `catalog.models.Track` directamente fue descartado por la misma razón.

## Conteo de módulos en el listado

**Decision**: Para mostrar la cantidad de módulos de cada track en el listado, la vista invoca `get_active_track(track.id)` una vez por cada track devuelto por `list_active_tracks()` y usa `len(track.active_modules)` (atributo ya prefetched por ese servicio). El detalle reutiliza la misma llamada que ya trae `active_modules`.

**Rationale**: `list_active_tracks()` solo proyecta los campos ligeros de listado (`TRACK_LEARNER_FIELDS`) y no incluye el conteo de módulos; `catalog` no puede modificarse en esta feature para añadir una variante agregada. Consumir `get_active_track` por track reutiliza exclusivamente superficie ya publicada, sin tocar `catalog`. El costo adicional es una consulta por track, aceptable dado el tamaño de catálogo de la línea base (dos tracks, especificado por la feature 005).

**Alternatives considered**: Añadir una función de agregación en `catalog.services.queries` fue descartado porque ese archivo está fuera de la lista de archivos que esta feature puede tocar. Anotar el conteo con una subconsulta propia sobre `catalog.models.Module` fue descartado porque violaría el principio 14.

## Idempotencia de la inscripción

**Decision**: `enroll(account, track)` intenta `Enrollment.objects.create(...)` dentro de `transaction.atomic()`; si la base de datos rechaza la fila por la restricción única `learning_enrollment_account_track_unique`, la función captura `IntegrityError` y devuelve la inscripción existente con `get_enrollment(account, track)`.

**Rationale**: El principio 5 exige que la garantía de unicidad la sostenga una restricción de base de datos capturada en transacción, no una comprobación previa en Python (que sería vulnerable a una carrera entre la lectura y la escritura). El criterio de aceptación solo exige comprobar dos envíos secuenciales, así que no se requiere una prueba de concurrencia real contra PostgreSQL para esta feature (a diferencia de la spec 010).

**Alternatives considered**: `Enrollment.objects.get_or_create(...)` fue descartado porque su comprobación previa seguida de creación no está documentada como atómica ante una restricción única bajo el nivel de aislamiento por defecto de PostgreSQL sin capturar explícitamente el conflicto; el patrón explícito de captura dentro de `atomic()` dejaría este comportamiento auditable y alineado con el mismo patrón que usarán las specs 009-010.

## Respuesta genérica ante track retirado o inexistente

**Decision**: Tanto el detalle como la inscripción usan `get_active_track(track_id)`; cuando devuelve `None` (id inexistente, no-UUID, o track no activo), la vista responde `HttpResponseNotFound` con el mismo mensaje genérico ya usado en `catalog/views.py` (`GENERIC_NOT_FOUND`), duplicando solo el texto de presentación, no la regla de negocio.

**Rationale**: El principio 12 exige una respuesta indistinguible ante falta de permiso o recurso inexistente. `get_active_track` ya colapsa "no existe" y "no está activo" en el mismo `None`, por lo que la vista no necesita (ni puede) distinguir ambos casos.

**Alternatives considered**: Devolver un mensaje distinto para "retirado" fue descartado porque violaría directamente el criterio de aceptación y el principio 12.

## Interacción HTMX de la tarjeta de inscripción

**Decision**: El botón de inscribirse vive dentro de un `<form method="post" action="..." hx-post="..." hx-target="#track-card-{{ track.id }}" hx-swap="outerHTML">{% csrf_token %}...</form>`, reutilizando exactamente el patrón ya establecido en `templates/catalog/partials/track_rows.html`. Sin JavaScript, el `POST` normal recibe una redirección `303` a la misma página; con HTMX, la respuesta es el fragmento `templates/learning/enrollment/partials/track_card.html` ya renderizado en su estado inscrito, y reemplaza solo esa tarjeta.

**Rationale**: El principio 11 exige mejora progresiva funcional sin JavaScript y reemplazo parcial vía HTMX; el patrón ya existe en el repositorio y evita introducir una convención nueva.

**Alternatives considered**: Recargar la página completa tras inscribirse fue descartado porque el criterio de interfaz pide reemplazar solo la tarjeta.

## Navegación

**Decision**: `learning/nav.py` añade un `NavItem` para `learning:enrollment-list` con `order=10`, antes de `learning-session` (30) y `learning-progress` (40).

**Rationale**: Refleja el flujo priorizado por la constitución (exploración → inscripción → sesión diaria → progreso) y usa el mismo mecanismo de descubrimiento ya validado por la feature 004.

**Alternatives considered**: Ninguna; es la única entrada de navegación que esta feature puede declarar.
