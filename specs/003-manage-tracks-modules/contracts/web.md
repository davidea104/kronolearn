# Web Contract: Administracion de tracks y modulos

**Date**: 2026-08-21
**Style**: HTML renderizado en servidor con mejora progresiva HTMX
**Data model**: [../data-model.md](../data-model.md)

## Reglas globales

- Todas las rutas requieren una cuenta autenticada y activa mediante `active_account_required`.
- Las rutas `catalog:manage-*` requieren ademas `CONTENT_ADMIN_ROLE`; no conceden acceso por pertenecer solo a `LEARNER_ROLE`.
- Toda mutacion usa `POST`, exige CSRF valido y deriva actor, permisos, estado y relaciones desde el servidor.
- Un POST valido desde HTML normal retorna `303 See Other` a una ruta GET canonica. Una solicitud HTMX valida puede retornar `200 OK` con el fragmento indicado y encabezado `HX-Push-Url` o `HX-Redirect` cuando corresponda.
- HTMX es una mejora de presentacion: `HX-Request`, targets y valores ocultos nunca sustituyen autenticacion, autorizacion, CSRF ni validacion.
- Los formularios de edicion envian `expected_revision`; los reordenamientos envian `expected_order_revision`. Ninguna revision recibida se escribe como revision nueva.
- Validacion de formulario retorna `200 OK` con resumen y errores asociados. Un token de revision obsoleto retorna `409 Conflict`, conserva la mutacion ganadora e indica recargar antes de reintentar.
- En cambios de estado, el servicio comprueba `expected_revision` antes de decidir si la solicitud es idempotente. Una revision obsoleta retorna `409` aunque el elemento ya tenga el estado solicitado; solo la revision vigente puede producir exito sin cambios.
- Las respuestas `403` y `404` usan texto generico, no reflejan referencias solicitadas ni incluyen datos, estados, revisiones, metadata o existencia de contenido protegido.
- Las rutas no admiten `DELETE`, y ningun formulario ofrece eliminacion permanente o traslado de modulos entre tracks.
- Todos los valores renderizados se escapan con Django. Los forms tienen labels explicitas, errores asociados y controles operables por teclado; JavaScript no es necesario.

## Respuestas de acceso

- Cuenta anonima o sesion de cuenta inactiva: `302 Found` a `/accounts/login/?next=<ruta-interna-segura>` despues de invalidar la sesion cuando aplica.
- Cuenta activa sin rol de administrador sobre cualquier ruta administrativa: `403 Forbidden` generico. La vista no carga entidades para un GET; un POST pasa la referencia opaca al servicio para producir un resultado auditado sin revelar existencia.
- Administrador con referencia administrativa UUID malformada o inexistente: `404 Not Found` generico; un POST produce exactamente un resultado auditado `NOT_FOUND` con un digest no reversible, nunca con la referencia cruda.
- Aprendiz que solicita contenido inexistente, inactivo o bajo un track inactivo: el mismo `404 Not Found` generico.
- Los POST anonimos o con CSRF invalido se detienen antes del servicio y no producen auditoria. Cada POST administrativo autenticado que supera CSRF y alcanza el servicio produce exactamente un `CatalogChangeLog`, incluso si termina `DENIED`, `INVALID`, `CONFLICT` o `NOT_FOUND`.

## Resumen de rutas del aprendiz

- **`catalog:track-list`**: `GET /learn/catalog/`; cuenta activa; retorna `200` con tracks activos ordenados.
- **`catalog:track-detail`**: `GET /learn/catalog/tracks/<str:track_id>/`; cuenta activa; retorna `200` con el track y sus modulos activos ordenados.
- **`catalog:module-detail`**: `GET /learn/catalog/tracks/<str:track_id>/modules/<str:module_id>/`; cuenta activa; retorna `200` con titulo y objetivo del modulo activo perteneciente al track activo.

## Catalogo del aprendiz

### GET `/learn/catalog/`

Renderiza `catalog/learner_track_list.html` con una proyeccion limitada a `id`, `title`, `description`, `audience` y `position`. La consulta filtra `Track.status = ACTIVE` y ordena por `(position, id)`.

### GET `/learn/catalog/tracks/<track_id>/`

Resuelve el track dentro del conjunto activo y renderiza `catalog/learner_track_detail.html`. La proyeccion del track coincide con la lista; cada modulo contiene solo `id`, `title`, `objective` y `position`, filtrado por `Module.status = ACTIVE` y ordenado por `(position, id)`.

### GET `/learn/catalog/tracks/<track_id>/modules/<module_id>/`

Resuelve en una sola consulta autorizada un modulo activo cuyo `track_id` coincide y cuyo track esta activo. Renderiza el detalle mediante la seccion de modulo de `catalog/learner_track_detail.html`; no acepta un track derivado del navegador como relacion confiable.

Para cualquiera de las dos rutas de detalle, UUID malformado, elemento inexistente, elemento inactivo o relacion padre-hijo incorrecta produce la misma respuesta `404`. Las vistas no consultan snapshots, revisiones ni auditoria para construir la respuesta.

Las referencias learner se capturan como `str` y se convierten a UUID dentro de las consultas autorizadas. Esto evita que el convertidor URL produzca una pagina 404 distinta antes de aplicar la respuesta generica y no cambia la forma de las URLs UUID validas.

## Resumen de rutas administrativas

- **`catalog:manage-track-list`**: `GET /catalog/manage/tracks/`.
- **`catalog:manage-track-create`**: `GET, POST /catalog/manage/tracks/new/`.
- **`catalog:manage-track-edit`**: `GET, POST /catalog/manage/tracks/<str:track_ref>/edit/`.
- **`catalog:manage-track-activate`**: `POST /catalog/manage/tracks/<str:track_ref>/activate/`.
- **`catalog:manage-track-deactivate`**: `POST /catalog/manage/tracks/<str:track_ref>/deactivate/`.
- **`catalog:manage-track-reorder`**: `POST /catalog/manage/tracks/<str:track_ref>/position/`.
- **`catalog:manage-module-list`**: `GET /catalog/manage/tracks/<str:track_ref>/modules/`.
- **`catalog:manage-module-create`**: `GET, POST /catalog/manage/tracks/<str:track_ref>/modules/new/`.
- **`catalog:manage-module-edit`**: `GET, POST /catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/edit/`.
- **`catalog:manage-module-activate`**: `POST /catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/activate/`.
- **`catalog:manage-module-deactivate`**: `POST /catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/deactivate/`.
- **`catalog:manage-module-reorder`**: `POST /catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/position/`.

Las referencias administrativas se capturan como `str` para que el servicio, no el convertidor URL, clasifique de forma uniforme referencias malformadas, autorizacion y auditoria. El valor crudo nunca se persiste ni refleja; cuando no se resuelve, el servicio conserva solamente su HMAC-SHA256 hexadecimal con proposito de clave dedicado.

## Listado administrativo de tracks

### GET `/catalog/manage/tracks/`

Renderiza `catalog/manage_track_list.html` con todos los tracks ordenados. Cada fila contiene titulo, estado, posicion, `revision`, enlaces de edicion/modulos y forms POST para mover o cambiar estado. La pagina contiene `track_order_revision` una sola vez como token de la secuencia.

Una solicitud con `HX-Request: true` y target permitido `track-rows` puede recibir solo `catalog/partials/track_rows.html`. Cualquier otro target recibe la pagina completa; el servidor no refleja nombres arbitrarios de template.

## Crear track

### GET `/catalog/manage/tracks/new/`

Renderiza `catalog/manage_track_form.html` con `title`, `description`, `audience` y CSRF. No expone estado, posicion, revisiones ni metadata editorial porque el track nace inactivo.

### POST `/catalog/manage/tracks/new/`

Acepta exclusivamente:

- `title`: obligatorio, maximo 160 despues de trim;
- `description`: obligatorio, maximo 2.000 despues de trim;
- `audience`: obligatorio, maximo 500 despues de trim;
- CSRF.

Campos extra como `id`, `status`, `position`, `revision`, `published_version`, `author` o `title_key` se descartan antes de validar. Exito retorna `303` al listado con confirmacion neutral. Error de datos o titulo duplicado retorna `200` con el formulario y no crea el track. Una colision concurrente se traduce al mismo error de titulo duplicado fuera del bloque atomico.

## Editar track

### GET `/catalog/manage/tracks/<track_ref>/edit/`

Renderiza los tres campos editables y `expected_revision` oculto. Si el track esta activo, muestra ademas `source`, `reviewed_on` y `editorial_status`; `editorial_status` ofrece solamente `APPROVED` en esta linea base. Autor y numero de version son de solo lectura y no se envian como autoridad.

### POST `/catalog/manage/tracks/<track_ref>/edit/`

Acepta los campos de contenido y:

- `expected_revision`: entero positivo obligatorio;
- `source`: texto libre obligatorio, maximo 500 despues de trim cuando el track esta activo; puede ser URL o referencia documental interna;
- `reviewed_on`: fecha ISO `YYYY-MM-DD`, obligatoria cuando esta activo y no futura;
- `editorial_status`: valor exacto `APPROVED` cuando esta activo.

El servidor decide si la metadata es obligatoria a partir del track bloqueado, no de un campo `status` recibido. En exito incrementa revision y, si estaba activo, publica el siguiente `TrackVersion`; retorna `303` al listado. Datos invalidos retornan `200`; conflicto de revision retorna `409` con los valores enviados, un mensaje de recarga y un enlace GET limpio. Ningun fallo altera contenido o versiones.

## Estado de track

### POST `.../<track_ref>/activate/`

Acepta CSRF, `expected_revision`, `source`, `reviewed_on` y `editorial_status=APPROVED`. El servicio comprueba primero la revision y exige al menos un modulo activo. Toda transicion real de inactivo a activo, incluida cada reactivacion, crea la siguiente version y retorna `303` al listado; si ya estaba activo con la revision vigente, retorna exito idempotente sin version nueva.

Metadata incompleta, fecha futura o ausencia de modulos activos retorna `200` con errores accionables y estado intacto. Revision obsoleta retorna `409`.

### POST `.../<track_ref>/deactivate/`

Acepta solo CSRF y `expected_revision`. El servicio comprueba primero la revision. Exito oculta el track sin cambiar estados de modulos ni versiones y retorna `303`; si ya estaba inactivo con revision vigente, es idempotente. Revision obsoleta retorna `409` aunque el track ya este inactivo.

## Reordenar tracks

### POST `.../<track_ref>/position/`

Acepta CSRF, `position` entero y `expected_order_revision`. El rango valido es `1..N`, donde `N` se calcula dentro de la transaccion. El actor no envia la secuencia completa.

- Exito HTML: `303` al listado.
- Exito HTMX: `200` con `catalog/partials/track_rows.html`, revision de orden nueva y anuncio accesible.
- Posicion no numerica o fuera de rango: `200` con el orden original y rango permitido.
- Revision de orden obsoleta: `409` con el orden vigente, mensaje de recarga y token vigente solo para el administrador autorizado.

## Listado y creacion de modulos

### GET `.../<track_ref>/modules/`

Renderiza `catalog/manage_module_list.html` para un track existente, incluidos modulos activos e inactivos ordenados. Cada fila contiene titulo, estado, posicion, revision y forms de acciones; la pagina contiene `track.module_order_revision`. HTMX puede solicitar exclusivamente `catalog/partials/module_rows.html` mediante el target permitido `module-rows`.

### GET `.../<track_ref>/modules/new/`

Renderiza `catalog/manage_module_form.html` con `title`, `objective` y CSRF. Track, estado, posicion y revisiones no son campos editables.

### POST `.../<track_ref>/modules/new/`

Acepta `title` obligatorio hasta 160, `objective` obligatorio hasta 1.000 y CSRF. El servicio resuelve y bloquea el track desde la URL, crea el modulo inactivo al final e incrementa la revision de orden. Exito retorna `303` al listado de modulos. Datos invalidos o titulo duplicado dentro del track retornan `200`; el mismo titulo en otro track es valido.

## Editar modulo

### GET `.../<track_ref>/modules/<module_ref>/edit/`

Exige que el modulo pertenezca al track resuelto. Renderiza `title`, `objective` y `expected_revision`; si esta activo, tambien solicita la metadata editorial descrita para track.

### POST `.../<track_ref>/modules/<module_ref>/edit/`

Acepta `title`, `objective`, `expected_revision` y, cuando el modulo bloqueado esta activo, `source`, `reviewed_on` y `editorial_status=APPROVED`. Ignora cualquier `track`, `position`, `status`, `author` o numero de version enviado.

Exito incrementa revision sin cambiar track, posicion o estado; si estaba activo, crea el siguiente `ModuleVersion`. Retorna `303` al listado de modulos. Validacion retorna `200`; revision obsoleta retorna `409` sin cambios.

## Estado de modulo

### POST `.../<module_ref>/activate/`

Acepta CSRF, `expected_revision` y metadata editorial completa. El servicio comprueba primero la revision. Puede activar el modulo aunque el track este inactivo; toda transicion real de inactivo a activo, incluida cada reactivacion, crea la siguiente version y retorna `303`. Una activacion idempotente con revision vigente no crea version; una revision obsoleta retorna `409` aunque ya este activo. Validacion retorna `200`.

### POST `.../<module_ref>/deactivate/`

Acepta CSRF y `expected_revision`. El servicio comprueba primero la revision. Si es el ultimo modulo activo de un track activo, retorna `200` con indicacion de activar otro modulo o desactivar primero el track. En otro caso desactiva sin reordenar, sin borrar versiones y retorna `303`. Una desactivacion idempotente con revision vigente no muta; una revision obsoleta retorna `409` aunque ya este inactivo.

## Reordenar modulos

### POST `.../<module_ref>/position/`

Acepta CSRF, `position` entero y `expected_order_revision`; el rango valido se deriva de los modulos del track bloqueado. La relacion entre `track_ref` y `module_ref` se valida en servidor.

- Exito HTML: `303` al listado de modulos.
- Exito HTMX: `200` con `catalog/partials/module_rows.html` y revision de orden nueva.
- Posicion invalida: `200` con secuencia intacta y rango permitido.
- Revision obsoleta: `409` con secuencia vigente y peticion de recarga.

## Matriz de resultados administrativos

- **`SUCCESS`, cambio aplicado**: `303` HTML o `200` fragmento HTMX; una auditoria con `changed=true`.
- **`SUCCESS`, operacion idempotente**: mismo destino observable; una auditoria con `changed=false`; no aumenta revision ni version.
- **`INVALID`**: `200`; errores de campo/accion; una auditoria `changed=false`.
- **`CONFLICT`**: `409`; mensaje de recarga, estado ganador intacto; una auditoria `changed=false`.
- **`NOT_FOUND`, administrador**: `404` generico; una auditoria `changed=false` con digest no reversible si se recibio una referencia, nunca con el valor crudo.
- **`DENIED`, cuenta activa sin rol**: `403` generico; una auditoria `changed=false`; no se revela si la entidad existe.

## Politica de retorno seguro

Se agregan como destinos GET permitidos por `accounts.security.resolve_safe_next()`:

- `catalog:track-list`: cualquier cuenta activa autenticada;
- `catalog:track-detail` y `catalog:module-detail`: cuenta activa y contenido resoluble dentro del catalogo activo;
- `catalog:manage-track-list`, forms y listados de modulos: cuenta activa con `CONTENT_ADMIN_ROLE`.

Ninguna ruta POST es destino de `next`. Un destino malformado, externo, inactivo o no autorizado cae en `ui:learner-home` sin reflejar el valor suministrado.

## Matriz de cobertura

- **FR-001, FR-013**: barreras de sesion/rol, CSRF, respuestas 403 genericas y auditoria de POST denegado.
- **FR-002, FR-003, FR-006, FR-007, FR-014, FR-019**: campos permitidos, limites, relaciones derivadas y errores atomicos de unicidad/validacion.
- **FR-004, FR-008, FR-018**: revision de orden, destino individual, secuencias vigentes y respuesta 409.
- **FR-005, FR-009, FR-017**: activacion, desactivacion idempotente, invariante del ultimo modulo y ausencia de delete.
- **FR-010, FR-011, FR-012**: proyecciones activas ordenadas y 404 indistinguible.
- **FR-015**: metadata obligatoria, fuente libre normalizada, autor servidor, secuencias por elemento, publicacion en cada activacion real y al editar contenido activo.
- **FR-016**: exactamente una auditoria por POST administrativo autenticado que alcanza el servicio y por resultado terminal; referencias no resueltas se conservan solo como digest no reversible.
