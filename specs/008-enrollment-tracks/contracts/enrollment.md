# Contract: Inscripción en tracks

## Rutas (`learning.urls.enrollment`, bajo el prefijo congelado `learn/enrollments/`)

| Método | Ruta | Nombre | Vista | Autenticación |
| --- | --- | --- | --- | --- |
| GET | `learn/enrollments/` | `learning:enrollment-list` | `enrollment_list` | `active_account_required` |
| GET | `learn/enrollments/tracks/<str:track_id>/` | `learning:enrollment-detail` | `enrollment_detail` | `active_account_required` |
| POST | `learn/enrollments/tracks/<str:track_id>/enroll/` | `learning:enrollment-enroll` | `enrollment_enroll` | `active_account_required` |

`learning:enrollment-list` es el nombre reservado por la feature 004 en `docs/contracts/domain-contracts.md`; `enrollment-detail` y `enrollment-enroll` son nombres nuevos, propios de esta feature, dentro de un archivo que ya pertenece a `learning`.

## Servicio (`learning.services.enrollment`)

```python
def enroll(account: Account, track: Track) -> Enrollment:
    """Crea o recupera la única inscripción activa de la cuenta en el track.

    Idempotencia: intenta crear la fila dentro de una transacción; si la restricción
    única `learning_enrollment_account_track_unique` la rechaza, devuelve la fila
    existente en vez de lanzar el conflicto o crear una segunda inscripción.
    No valida elegibilidad de negocio adicional: la vista ya resolvió el track
    exclusivamente a través de `catalog.services.queries.get_active_track`, por lo
    que un track retirado o inexistente nunca llega a esta función.
    """
```

`get_enrollment(account, track)` y `list_enrollments(account)` no cambian de firma ni de comportamiento; esta feature los consume tal cual.

## Vistas (`learning.views.enrollment`)

- **`enrollment_list(request)`**: `GET` únicamente. Obtiene `catalog.services.queries.list_active_tracks()`, adjunta `module_count` e `is_enrolled` por track (ver `data-model.md`) y renderiza `learning/enrollment/list.html`. Sin tracks activos, la plantilla usa el estado vacío compartido.
- **`enrollment_detail(request, track_id)`**: `GET` únicamente. Resuelve el track con `get_active_track(track_id)`; si es `None`, responde `HttpResponseNotFound` con un mensaje genérico propio (ver nota abajo). En caso contrario, calcula `is_enrolled` y renderiza `learning/enrollment/detail.html`.
- **`enrollment_enroll(request, track_id)`**: `POST` únicamente (`require_POST`). Resuelve el track con `get_active_track(track_id)`; si es `None`, responde el mismo `HttpResponseNotFound` genérico, sin crear inscripción. En caso contrario, llama a `enroll(request.user, track)` y responde:
  - Si `request.headers.get("HX-Request") == "true"`: renderiza `learning/enrollment/partials/track_card.html` con `is_enrolled=True`, con estado `200`, reemplazando solo esa tarjeta (`hx-target="#track-card-{{ track.id }}"`, `hx-swap="outerHTML"`).
  - En otro caso: `HttpResponseSeeOther` (`303`) de vuelta a `learning:enrollment-detail` para ese track, replicando el patrón ya usado en `catalog/views.py`.

Ninguna vista decide autorización por sí misma más allá de `active_account_required`: la identidad siempre proviene de `request.user`; ningún formulario ni URL transporta un identificador de cuenta.

## Plantillas (`templates/learning/enrollment/`)

- **`list.html`**: extiende `base.html`; itera las tarjetas usando `ui/components/card.html` como contenedor; cada tarjeta incluye `partials/track_card.html` con `track`, `module_count`, `is_enrolled`. Sin tracks, usa `ui/components/empty_state.html`.
- **`detail.html`**: extiende `base.html`; muestra título, descripción, cantidad de módulos y el mismo bloque de acción de `partials/track_card.html` (o su botón de inscribirse/estado inscrito) para ese track.
- **`partials/track_card.html`**: fragmento HTMX-swappable con `id="track-card-{{ track.id }}"`; si `is_enrolled` es verdadero, muestra el estado "Inscrito" con icono y texto (nunca solo color, según el principio 11); si es falso, muestra el formulario `POST` hacia `learning:enrollment-enroll` con el botón "Inscribirme" (`ui/components/button.html`, `type="submit"`).

## Errores y respuestas genéricas

| Caso | Respuesta |
| --- | --- |
| Track retirado | `404` con el mensaje genérico propio de esta feature |
| Track inexistente (UUID inválido o no encontrado) | La misma `404` genérica, idéntica a la anterior |
| Envío repetido de inscripción (mismo par cuenta-track) | `200`/`303` de éxito, sin error, sin segunda fila |
| Intento de inscribir a otra cuenta | Imposible por diseño: la cuenta siempre es `request.user` |
| Solicitud anónima (GET o POST) | Redirección al login vía `active_account_required`, conservando `next` |

**Nota sobre el mensaje genérico**: `learning/views/enrollment.py` DEBE definir su propia constante de mensaje (p. ej. `GENERIC_NOT_FOUND = "No se encontró el recurso solicitado."`), duplicando solo el texto ya usado en `catalog/views.py`. Esta feature NUNCA importa `catalog.views.GENERIC_NOT_FOUND` ni ningún otro símbolo de `catalog/views.py`: ese archivo está cerrado, y el principio 14 exige que las lecturas entre módulos pasen por servicios de consulta publicados, no por los internos de la vista de otra app.
