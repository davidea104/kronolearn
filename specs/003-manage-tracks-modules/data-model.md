# Data Model: Administracion de tracks y modulos

## Convenciones

- Todos los identificadores de dominio usan UUID no editables.
- Todos los timestamps usan zona horaria y se asignan en servidor.
- `ACTIVE` e `INACTIVE` son los unicos estados de disponibilidad de tracks y modulos.
- `APPROVED` es el unico estado editorial publicable de esta linea base.
- `title_key` se deriva con `title.strip().casefold()` y nunca se recibe como dato confiable del navegador.
- `revision` comienza en 1 y aumenta tras cada mutacion aceptada del elemento.
- `published_version` comienza en 0 y aumenta exactamente en uno al crear un snapshot publicado.
- `source` se persiste sin espacios exteriores como texto libre no vacio de hasta 500 caracteres; puede ser una URL o una referencia documental interna.
- Los servicios son la unica superficie de escritura de dominio; vistas, forms y admin no escriben modelos directamente.

## CatalogState

Registro tecnico singleton que serializa la secuencia global de tracks.

- **`id`** (entero pequeno): clave primaria fija en `1`; no editable.
- **`track_order_revision`** (entero positivo grande): comienza en `0`; aumenta al crear o reordenar tracks.

**Constraints**:

- `id = 1`.
- `track_order_revision >= 0`.
- La migracion inicial crea el registro; los fixtures de pruebas transaccionales lo restauran en `setUp()`.

## Track

Ruta mutable de aprendizaje y raiz de una secuencia de modulos.

- **`id`** (UUID): clave primaria; generado en servidor.
- **`title`** (texto, 160): obligatorio; sin espacios exteriores persistidos.
- **`title_key`** (texto, 480): derivado; unico en todo el catalogo; no editable.
- **`description`** (texto, 2.000): obligatorio.
- **`audience`** (texto, 500): obligatorio; descripcion editorial, no regla de acceso.
- **`status`** (enum): `INACTIVE` por defecto o `ACTIVE`.
- **`position`** (entero positivo): unico global; secuencia consecutiva desde 1.
- **`revision`** (entero positivo grande): comienza en 1; token de edicion optimista.
- **`module_order_revision`** (entero positivo grande): comienza en 0; token de la secuencia de modulos.
- **`published_version`** (entero positivo): comienza en 0; ultimo numero publicado.
- **`created_at`** (fecha/hora): asignado al crear.
- **`updated_at`** (fecha/hora): actualizado al mutar el track.

**Constraints e indices**:

- Unicidad de `title_key`.
- Unicidad de `position`.
- Checks `position >= 1`, `revision >= 1`, `module_order_revision >= 0` y `published_version >= 0`.
- Un track `ACTIVE` requiere `published_version >= 1`; la existencia de al menos un modulo activo se valida bajo bloqueo en servicio porque cruza filas.
- Indice `(status, position)` para catalogo del aprendiz.
- Orden por defecto `(position, id)`; `id` actua como desempate defensivo aunque la posicion sea unica.

## Module

Unidad mutable perteneciente a un unico track.

- **`id`** (UUID): clave primaria; generado en servidor.
- **`track`** (FK a Track): obligatoria; `PROTECT`; no cambia despues de crear.
- **`title`** (texto, 160): obligatorio; sin espacios exteriores persistidos.
- **`title_key`** (texto, 480): derivado; unico dentro del track; no editable.
- **`objective`** (texto, 1.000): obligatorio.
- **`status`** (enum): `INACTIVE` por defecto o `ACTIVE`.
- **`position`** (entero positivo): unico dentro del track; secuencia consecutiva desde 1.
- **`revision`** (entero positivo grande): comienza en 1; token de edicion optimista.
- **`published_version`** (entero positivo): comienza en 0; ultimo numero publicado.
- **`created_at`** (fecha/hora): asignado al crear.
- **`updated_at`** (fecha/hora): actualizado al mutar el modulo.

**Constraints e indices**:

- Unicidad de `(track, title_key)` y `(track, position)`.
- Checks `position >= 1`, `revision >= 1` y `published_version >= 0`.
- Un modulo `ACTIVE` requiere `published_version >= 1`.
- Indice `(track, status, position)` para detalle del aprendiz.
- Orden por defecto `(track_id, position, id)`.

## TrackVersion

Snapshot append-only de los datos editoriales de un track en una publicacion.

- **`id`** (UUID): clave primaria; generado en servidor.
- **`track`** (FK a Track): obligatoria; `PROTECT`; related name `versions`.
- **`version_number`** (entero positivo): secuencia del track desde 1.
- **`title`** (texto, 160): copia publicada.
- **`description`** (texto, 2.000): copia publicada.
- **`audience`** (texto, 500): copia publicada.
- **`author`** (FK a Account): actor autenticado; `PROTECT`.
- **`source`** (texto, 500): obligatorio; texto libre normalizado con referencia o URL editorial.
- **`reviewed_on`** (fecha): obligatoria; confirmada por administrador.
- **`editorial_status`** (enum): debe ser `APPROVED`.
- **`published_at`** (fecha/hora): asignado en servidor al publicar.

**Constraints e indices**:

- Unicidad de `(track, version_number)`.
- Check `version_number >= 1`.
- Indice `(track, -version_number)` para resolver la version vigente e historial.
- Solo permiso `view`; no existen comandos de update/delete y el modelo rechaza mutar una instancia persistida.

## ModuleVersion

Snapshot append-only de los datos editoriales de un modulo en una publicacion.

- **`id`** (UUID): clave primaria; generado en servidor.
- **`module`** (FK a Module): obligatoria; `PROTECT`; related name `versions`.
- **`version_number`** (entero positivo): secuencia del modulo desde 1.
- **`title`** (texto, 160): copia publicada.
- **`objective`** (texto, 1.000): copia publicada.
- **`author`** (FK a Account): actor autenticado; `PROTECT`.
- **`source`** (texto, 500): obligatorio; texto libre normalizado con referencia o URL editorial.
- **`reviewed_on`** (fecha): obligatoria; confirmada por administrador.
- **`editorial_status`** (enum): debe ser `APPROVED`.
- **`published_at`** (fecha/hora): asignado en servidor al publicar.

**Constraints e indices**:

- Unicidad de `(module, version_number)`.
- Check `version_number >= 1`.
- Indice `(module, -version_number)`.
- Solo permiso `view`; no existen comandos de update/delete y el modelo rechaza mutar una instancia persistida.

## CatalogChangeLog

Evidencia append-only de todo comando administrativo autenticado.

- **`id`** (UUID): clave primaria; generado en servidor.
- **`actor`** (FK a Account): obligatoria; `PROTECT`.
- **`action`** (enum): `CREATE`, `EDIT`, `ACTIVATE`, `DEACTIVATE` o `REORDER`.
- **`entity_type`** (enum): `TRACK` o `MODULE`.
- **`entity_id`** (UUID nullable): elemento resuelto o creado; nulo si no se asigno o la referencia no pudo resolverse.
- **`unresolved_reference_digest`** (texto ASCII, 64, nullable): HMAC-SHA256 en hexadecimal de una referencia solicitada inexistente o malformada, con proposito de clave dedicado; nunca contiene el valor crudo.
- **`result`** (enum): `SUCCESS`, `DENIED`, `INVALID`, `CONFLICT` o `NOT_FOUND`.
- **`changed`** (booleano): verdadero solo cuando `result = SUCCESS` y hubo mutacion.
- **`occurred_at`** (fecha/hora): asignado al registrar el resultado.

**Constraints e indices**:

- Un resultado distinto de `SUCCESS` exige `changed = false`.
- `changed = true` exige `result = SUCCESS` y `entity_id` no nulo.
- `entity_id` y `unresolved_reference_digest` no pueden coexistir; ambos pueden ser nulos solo cuando la accion no tenia referencia resoluble, como un create rechazado antes de asignar UUID.
- Indices `(actor, occurred_at)`, `(entity_type, entity_id, occurred_at)`, `(entity_type, unresolved_reference_digest, occurred_at)` y `(result, occurred_at)`.
- Solo permiso `view`; no hay superficies de update/delete.
- No almacena titulo, metadata enviada ni otros payloads; evita duplicacion y reduce exposicion.

## Relaciones

```text
CatalogState (1 singleton)

Track 1 ──── * Module
  │              │
  │              └──── * ModuleVersion
  └──── * TrackVersion

Account 1 ──── * TrackVersion
Account 1 ──── * ModuleVersion
Account 1 ──── * CatalogChangeLog
```

- `Track` y `Module` nunca se eliminan mediante esta feature.
- `PROTECT` impide borrar actores o entidades que sostienen historial publicado.
- `CatalogChangeLog.entity_id` es una referencia historica deliberadamente no relacional al elemento resuelto, incluso cuando la operacion sobre el termino con un resultado fallido.
- `CatalogChangeLog.unresolved_reference_digest` permite correlacionar de forma no reversible solicitudes repetidas que no resolvieron una entidad; se calcula en servidor y nunca se muestra en respuestas web.
- Posicion no forma parte del snapshot editorial: el historial de aprendizaje referencia el contenido exacto, mientras el orden representa la presentacion vigente del catalogo.
- La integracion futura de intentos en `learning` DEBE guardar una FK protegida a `TrackVersion` o `ModuleVersion`, segun el contenido presentado. Crear esa relacion queda fuera de esta feature, que entrega las versiones inmutables como contrato de integracion.

## Transiciones de Track

### Crear track

1. Revalidar que el actor tenga `CONTENT_ADMIN_ROLE`.
2. Bloquear `CatalogState`.
3. Normalizar y validar campos; asignar `position = max(position) + 1`.
4. Crear `INACTIVE`, `revision = 1`, `module_order_revision = 0`, `published_version = 0`.
5. Incrementar `track_order_revision` y registrar auditoria.

### Editar track

1. Bloquear actor y track; comparar `expected_revision`.
2. Validar titulo normalizado y textos.
3. Si esta `ACTIVE`, exigir metadata, incrementar `published_version` y crear `TrackVersion` con los valores nuevos.
4. Persistir campos, incrementar `revision` y registrar auditoria.
5. Si esta `INACTIVE`, no crear snapshot.

### Activar track

1. Bloquear track y sus modulos; comparar `expected_revision` antes de evaluar el estado solicitado.
2. Si la revision esta obsoleta, devolver `CONFLICT` aunque el track ya este `ACTIVE`.
3. Si ya esta `ACTIVE` con revision vigente, devolver exito sin cambios ni nueva version.
4. Exigir al menos un modulo `ACTIVE` y metadata completa.
5. Cambiar de `INACTIVE` a `ACTIVE`, incrementar `revision` y `published_version`, crear snapshot y auditar atomicamente, tanto en la primera activacion como en cada reactivacion posterior.

### Desactivar track

1. Bloquear y comparar revision antes de evaluar el estado solicitado.
2. Si la revision esta obsoleta, devolver `CONFLICT` aunque el track ya este `INACTIVE`.
3. Si ya esta `INACTIVE` con revision vigente, devolver exito sin cambios.
4. Cambiar a `INACTIVE`, incrementar `revision` y auditar; conservar estados de modulos y snapshots.

### Reordenar tracks

1. Bloquear `CatalogState` y todos los tracks en orden estable por UUID.
2. Comparar `expected_order_revision`, validar elemento y posicion destino.
3. Trasladar temporalmente posiciones a un rango positivo libre y escribir `1..N`.
4. Incrementar la revision de los tracks cuya posicion cambio y `track_order_revision` una vez.
5. Auditar el track solicitado. Cualquier error revierte la secuencia completa.

## Transiciones de Module

### Crear modulo

1. Bloquear actor, track padre y modulos del track.
2. Normalizar y validar; asignar al final de la secuencia.
3. Crear `INACTIVE`, `revision = 1`, `published_version = 0`.
4. Incrementar `track.module_order_revision` y auditar.

### Editar modulo

1. Bloquear actor y modulo; comparar `expected_revision`.
2. Mantener `track` y `position` sin cambios; validar titulo y objetivo.
3. Si esta `ACTIVE`, exigir metadata, incrementar `published_version` y crear `ModuleVersion` con valores nuevos.
4. Incrementar `revision` y auditar. Si esta `INACTIVE`, no crear snapshot.

### Activar modulo

1. Bloquear modulo y track; comparar revision antes de evaluar el estado solicitado.
2. Si la revision esta obsoleta, devolver `CONFLICT` aunque el modulo ya este `ACTIVE`.
3. Si ya esta `ACTIVE` con revision vigente, devolver exito sin cambios.
4. Exigir metadata y cambiar de `INACTIVE` a `ACTIVE`; incrementar `revision` y `published_version`, crear snapshot y auditar, tanto en la primera activacion como en cada reactivacion posterior.
5. El track puede estar inactivo; el modulo no sera visible hasta activar el track.

### Desactivar modulo

1. Bloquear track y sus modulos; comparar revision antes de evaluar el estado solicitado.
2. Si la revision esta obsoleta, devolver `CONFLICT` aunque el modulo ya este `INACTIVE`.
3. Si ya esta `INACTIVE` con revision vigente, devolver exito sin cambios.
4. Si es el ultimo modulo activo de un track `ACTIVE`, devolver `INVALID` sin cambios.
5. Cambiar a `INACTIVE`, incrementar `revision` y auditar.

### Reordenar modulos

1. Bloquear track padre y todos sus modulos en orden estable por UUID.
2. Comparar `expected_order_revision` con `module_order_revision`; validar destino.
3. Aplicar desplazamiento positivo temporal y escribir posiciones consecutivas.
4. Incrementar revision de modulos movidos y `module_order_revision` una vez.
5. Auditar el modulo solicitado y revertir todo ante error.

## Visibilidad del aprendiz

- Lista: `Track.status = ACTIVE`, orden `(position, id)`.
- Detalle: resolver primero el track con filtro `ACTIVE`; un UUID inactivo e inexistente produce el mismo resultado no encontrado.
- Modulos: `Module.status = ACTIVE` y track activo, orden `(position, id)`.
- Las consultas nunca entregan `title_key`, revisiones, metadata editorial, versiones ni auditoria a templates del aprendiz.
- Desactivar afecta la siguiente consulta; no modifica snapshots ni referencias historicas.

## Resultado de comandos

Los servicios retornan un objeto inmutable con:

- `result`: uno de los codigos de `CatalogChangeLog.Result`;
- `changed`: si hubo mutacion;
- `entity_type` y `entity_id`;
- `revision`: revision vigente cuando puede revelarse al administrador autorizado;
- `field_errors`: mapa de errores para formularios administrativos;
- `order_revision`: revision vigente de la secuencia cuando aplica.

Cada solicitud autenticada que supera las protecciones previas y alcanza un servicio registra exactamente un `CatalogChangeLog` antes de devolver. Las solicitudes detenidas antes del servicio no generan auditoria de dominio. Una excepcion tecnica no capturada revierte tanto datos como auditoria y se trata como fallo operativo, no como resultado de negocio.
