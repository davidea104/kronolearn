# Phase 0 Research: Administracion de tracks y modulos

## Fuentes revisadas

- Patrones locales: `accounts/models.py`, `accounts/services/roles.py`, `accounts/views.py`, `accounts/security.py`, `kronolearn/settings/base.py` y `.github/workflows/ci.yml`.
- Django 5.2: [transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), [`select_for_update()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) y [validacion de modelos](https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects).

## Decision 1: Frontera de dominio

**Decision**: `catalog` sera propietario de modelos, consultas y servicios de mutacion. Las vistas comprobaran sesion y rol para la respuesta HTTP, y los servicios volveran a comprobar el actor antes de mutar y auditar. `ui` solo enlazara el catalogo desde el inicio del aprendiz.

**Rationale**: Sigue el monolito modular constitucional y el patron local de vistas delgadas que delegan reglas atomicas a servicios. La segunda comprobacion en servicio evita que una llamada interna omita autorizacion y permite auditar intentos denegados.

**Alternatives considered**:

- Implementar reglas en vistas: rechazado porque duplicaria logica y violaria la constitucion.
- Usar solo Django Admin: rechazado porque no cubre el contrato HTMX, la deteccion de cambios obsoletos ni los flujos del aprendiz.
- Crear una API o frontend separado: rechazado por alcance y por la restriccion de monolito.

## Decision 2: Registros mutables y snapshots publicados

**Decision**: `Track` y `Module` conservaran el estado de trabajo actual. `TrackVersion` y `ModuleVersion` guardaran snapshots publicados separados, inmutables y numerados por elemento. Las referencias historicas futuras apuntaran directamente al snapshot correspondiente.

**Rationale**: Un contador en la entidad no preserva valores historicos. Los modelos separados permiten editar contenido inactivo sin alterar publicaciones previas y siguen el patron append-only de `RoleChangeLog`.

**Alternatives considered**:

- Guardar solo el numero vigente en `Track`/`Module`: rechazado porque no conserva el contenido exacto presentado.
- Un modelo generico de version con `GenericForeignKey`: rechazado porque reduce integridad referencial y complica constraints.
- Copiar toda la jerarquia en cada publicacion: rechazado porque la version pertenece a cada elemento y multiplicaria datos sin necesidad.

## Decision 3: Concurrencia optimista y bloqueo

**Decision**: Cada `Track` y `Module` tendra un entero `revision` enviado como campo oculto en ediciones y cambios de estado. Un `CatalogState` singleton mantendra `track_order_revision`; cada `Track` mantendra `module_order_revision`. Los servicios bloquearan las filas relevantes con `select_for_update()` dentro de `transaction.atomic()`, compararan la revision esperada antes de evaluar si el estado solicitado ya coincide y devolveran conflicto sin cambios cuando no coincida. Solo una solicitud con revision vigente puede terminar como exito idempotente sin mutacion.

**Rationale**: Las revisiones enteras son deterministas y evitan la precision variable de timestamps. El singleton permite serializar el primer alta y el orden global incluso cuando aun no existen tracks; bloquear el track padre cumple la misma funcion para sus modulos. Django documenta que `select_for_update()` requiere una transaccion y que no tiene efecto real en SQLite, por lo que la semantica de bloqueo se comprobara tambien en PostgreSQL.

**Alternatives considered**:

- Ultima escritura gana: rechazado por la aclaracion de conflicto.
- Timestamps como token: rechazado por precision, conversion de zona horaria y comparaciones menos explicitas.
- Bloqueo de interfaz por administrador: rechazado porque requiere leases, expiracion y recuperacion sin aportar valor al volumen previsto.
- Bloquear solo todas las filas Track: rechazado porque una coleccion vacia no ofrece fila que bloquear.

## Decision 4: Identidad normalizada de titulos

**Decision**: Persistir `title_key = title.strip().casefold()` como campo no editable. Sera unico globalmente en `Track` y unico por `track` en `Module`; los servicios calcularan la clave y la base de datos aplicara `UniqueConstraint` para cerrar carreras.

**Rationale**: La clave persistida produce la misma semantica en PostgreSQL y SQLite, incluidas variantes Unicode que no se comportan igual con comparaciones case-insensitive de cada backend. La validacion de formulario ofrece el error temprano y la constraint garantiza integridad concurrente.

**Alternatives considered**:

- `Lower(title)` como unica regla: rechazado porque no elimina espacios exteriores y difiere para Unicode entre backends.
- Validacion solo en formulario: rechazada porque dos solicitudes concurrentes podrian crear duplicados.
- Slugs publicos: rechazados porque no son requisito y los UUID ya identifican recursos.

## Decision 5: Ordenamiento sin posiciones transitorias invalidas

**Decision**: `position` sera entero positivo con unicidad global para tracks y unicidad por track para modulos. Crear agrega al final bajo bloqueo. Reordenar bloqueara el contexto, validara revision y rango, movera temporalmente las posiciones a un rango positivo libre y escribira despues la secuencia final consecutiva.

**Rationale**: El desplazamiento positivo en dos fases evita colisiones de unicidad durante intercambios y funciona tanto en PostgreSQL como en SQLite. Las constraints comprueban el estado persistido y el servicio conserva atomicidad.

**Alternatives considered**:

- Constraints diferibles: rechazadas porque SQLite las ignora y la suite rapida perderia equivalencia.
- Posiciones decimales o con huecos: rechazadas porque el spec exige enteros consecutivos desde uno.
- Reescribir orden desde la vista: rechazado porque la operacion debe ser atomica y reutilizable.

## Decision 6: Publicacion y metadatos editoriales

**Decision**: Toda transicion real de `INACTIVE` a `ACTIVE` y toda edicion aceptada de contenido activo requerira `source`, `reviewed_on` y confirmacion de estado `APPROVED`. El servicio asignara `author` desde el actor autenticado, incrementara `published_version` y creara el snapshot en la misma transaccion. Repetir una activacion con revision vigente mientras el elemento ya esta activo sera un exito sin cambios ni snapshot; editar contenido inactivo no creara snapshot.

**Rationale**: Cumple la aclaracion y asegura que nunca exista una version publicada sin los cinco datos constitucionales. `APPROVED` es el unico estado editorial publicable de esta linea base; un flujo de borrador/revision esta fuera de alcance.

**Alternatives considered**:

- Reutilizar metadatos anteriores: rechazado porque puede conservar una fuente o revision desactualizada.
- Guardar metadata solo en la entidad mutable: rechazado porque el historial perderia contexto.
- Agregar workflow editorial multietapa: rechazado por YAGNI y por el limite explicito de estados.

## Decision 7: Inmutabilidad y auditoria

**Decision**: Los snapshots y `CatalogChangeLog` tendran permisos por defecto de solo lectura, claves foraneas `PROTECT` y no se expondran a servicios de actualizacion o borrado. Cada POST autenticado con CSRF valido que alcance el servicio registrara actor, accion, tipo de elemento, resultado, indicador de cambio y fecha. Si el elemento se resuelve, registrara su UUID; si la referencia es inexistente o malformada, registrara solo un digest HMAC-SHA256 no reversible con proposito dedicado. Las solicitudes anonimas o rechazadas por CSRF no alcanzaran el servicio ni crearan auditoria; resultados fallidos no podran indicar cambios.

**Rationale**: Replica la evidencia append-only de roles y permite probar exitos, validaciones, conflictos y denegaciones sin almacenar payloads privados innecesarios.

**Alternatives considered**:

- Un log JSON con copias completas: rechazado por duplicacion, privacidad y contratos mas debiles.
- Solo logging de aplicacion: rechazado porque no garantiza trazabilidad persistente.
- Senales Django para auditoria: rechazadas porque ocultan el actor y el limite transaccional del caso de uso.
- Persistir la referencia solicitada en claro: rechazado porque expone input no confiable y no es necesario para correlacionar intentos repetidos.

## Decision 8: Consultas activas como contrato de dominio

**Decision**: `catalog/services/queries.py` ofrecera consultas administrativas y del aprendiz. La consulta del aprendiz filtrara tracks `ACTIVE`, prefetcheara solo modulos `ACTIVE` y ordenara ambos por `position`; el detalle aplicara el mismo filtro al identificador antes de devolver contenido.

**Rationale**: Centralizar el filtro evita que una vista futura exponga contenido inactivo. `Prefetch` con queryset filtrado mantiene un numero acotado de consultas para 100 tracks y 5.000 modulos.

**Alternatives considered**:

- Filtrar en templates: rechazado porque los objetos inactivos ya habrian cruzado la frontera de presentacion.
- Filtrar por separado en cada vista: rechazado por riesgo de divergencia.
- Manager global que oculte inactivos: rechazado porque administracion necesita consultar ambos estados y un manager por defecto oculto puede afectar migraciones y relaciones.

## Decision 9: Validacion, resultados y errores HTTP

**Decision**: `ModelForm` validara campos editables y metadata; los servicios validaran reglas de estado, revision, posicion y autorizacion. Las fallas esperadas se expresaran mediante resultados inmutables con codigos `SUCCESS`, `DENIED`, `INVALID`, `CONFLICT` y `NOT_FOUND`, mas errores de campo cuando correspondan. Las vistas traduciran esos resultados a formulario, 403, 404, 409 o redireccion 303; HTMX recibira el mismo fragmento y estado observable.

**Rationale**: Conserva la separacion HTTP/dominio, evita usar excepciones para ramas normales y sigue los resultados inmutables de `accounts.services.roles`. Los `ModelForm` ejecutan validacion de campos y constraints, pero la base de datos sigue siendo la autoridad ante carreras.

**Alternatives considered**:

- Excepciones para toda falla de negocio: rechazadas porque hacen opacas las ramas esperadas y la auditoria.
- Mensajes generados dentro del servicio: rechazados porque acoplan dominio e interfaz.
- Responder 200 a conflictos: rechazado porque dificulta distinguir una edicion obsoleta en pruebas e integraciones HTMX.

## Decision 10: Estrategia de pruebas y entrega

**Decision**: Usar `TestCase` para modelos, servicios, consultas y vistas; `TransactionTestCase` contra PostgreSQL para bloqueos/concurrencia; `Client(enforce_csrf_checks=True)` para mutaciones web; y la matriz CI existente para Ruff, checks, migraciones y suite. No se agregaran paquetes.

**Rationale**: Sigue la base instalada y evita introducir factories o runners. Django advierte que `TestCase` envuelve cada prueba en una transaccion y puede ocultar errores de `select_for_update()`, mientras SQLite no aplica el bloqueo de filas.

**Alternatives considered**:

- Probar concurrencia solo en SQLite: rechazado porque `select_for_update()` no tiene efecto.
- Agregar pytest/factory libraries: rechazado porque no son necesarias para el alcance y rompen la linea base de dependencias.
- Validacion solo manual: rechazada por la constitucion y por el riesgo de orden/versionado.

## Decision 11: Invariante de track activo

**Decision**: Un track activo conservara al menos un modulo activo. El servicio rechazara desactivar el ultimo modulo activo mientras su track siga activo e indicara activar otro modulo o desactivar primero el track.

**Rationale**: Extiende de forma coherente la condicion de activacion del spec y evita mostrar rutas activas vacias. La regla pertenece al servicio porque depende del estado agregado de varios modulos.

**Alternatives considered**:

- Permitir un track activo vacio: rechazado porque contradice la condicion de ruta lista para publicarse.
- Desactivar automaticamente el track: rechazado porque introduce un cambio de estado no solicitado y una auditoria implicita sorprendente.

## Decision 12: Limites de texto

**Decision**: Usar 160 caracteres para titulos, 2.000 para descripcion de track, 500 para audiencia, 1.000 para objetivo de modulo y 500 para fuente editorial. Los valores se validaran despues de eliminar espacios exteriores; los campos obligatorios no aceptaran texto vacio. La fuente aceptara texto libre, incluida una URL o referencia documental interna, sin imponer formato URL.

**Rationale**: Son limites suficientes para contenido editorial breve, evitan payloads sin cota y convierten la delegacion del spec en criterios compartidos por formularios, modelos y pruebas.

**Alternatives considered**:

- Campos sin limite contractual: rechazados porque harian ambiguos los errores de aceptacion.
- Limites mucho menores: rechazados porque descripcion, objetivo y fuente pueden requerir contexto legible.
- Contenido enriquecido en esta feature: rechazado porque no se solicito formato ni edicion avanzada.

## Decision 13: Protocolo de rendimiento reproducible

**Decision**: Preparar un catalogo de 100 tracks con 50 modulos por track, ejecutar 20 solicitudes de calentamiento no medidas y medir despues 200 solicitudes validas: 50 creaciones, 50 ediciones, 50 reordenamientos y 50 cambios de estado. La medicion usara PostgreSQL y configuracion equivalente a produccion, abarcara desde la recepcion de la solicitud hasta completar la respuesta del servidor y excluira red publica. La evidencia registrara capacidad/configuracion del entorno, observaciones y percentil 95.

**Rationale**: Fija muestra, mezcla, frontera y entorno para que el objetivo de menos de dos segundos sea reproducible sin convertir latencia externa variable en una propiedad del dominio.

**Alternatives considered**:

- Operaciones manuales sin distribucion fija: rechazadas porque no producen una muestra comparable ni un percentil estable.
- Medicion extremo a extremo sobre Railway: rechazada como gate porque mezcla red publica y carga compartida fuera del control de la aplicacion.
- Agregar una dependencia de carga en Phase 0: rechazado; el harness puede implementarse con la herramienta estandar elegida durante tareas sin cambiar el contrato de medicion.

## Resultado de Phase 0

Todas las decisiones tecnicas necesarias para Phase 1 estan resueltas. No quedan marcadores de aclaracion.
