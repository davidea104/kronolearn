# Feature Specification: Administracion de tracks y modulos

**Feature Branch**: `003-manage-tracks-modules`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "Como administrador de contenido, quiero crear y ordenar tracks y modulos para estructurar rutas de aprendizaje. El administrador puede crear, editar y desactivar tracks; puede crear, editar, ordenar y desactivar modulos dentro de un track; un track registra titulo, descripcion, audiencia y estado; un modulo registra titulo, objetivo y posicion; un aprendiz solo ve tracks y modulos activos; y un aprendiz no puede acceder a las acciones administrativas."

## Clarifications

### Session 2026-08-21

- Q: ¿Que debe ocurrir cuando dos administradores editan o reordenan el mismo track o modulo partiendo de versiones diferentes? → A: Rechazar el cambio obsoleto, conservar el primero aceptado y pedir recargar antes de reintentar.
- Q: ¿Deben permitirse titulos repetidos para tracks o para modulos dentro del mismo track? → A: Los titulos de track son unicos en el catalogo y los titulos de modulo son unicos dentro de cada track, ignorando mayusculas y espacios exteriores.
- Q: ¿Como debe asignarse el numero de cada version publicada de un track o modulo? → A: Cada elemento tiene su propia secuencia, empieza en 1 e incrementa en uno con cada publicacion.
- Q: ¿Que debe hacer el administrador con los metadatos editoriales al editar un track o modulo que ya esta activo? → A: Confirmar fuente, fecha de revision y estado editorial antes de publicar; autor y numero se asignan automaticamente.
- Q: ¿Cuando debe crear una nueva version publicada la reactivacion de un track o modulo? → A: Toda transicion real de inactivo a activo crea la siguiente version publicada aunque el contenido no haya cambiado; repetir la activacion mientras ya esta activo no crea otra version.
- Q: ¿Que solicitudes administrativas deben generar auditoria y como debe representarse un elemento inexistente o malformado? → A: Cada solicitud de cambio autenticada que supera la proteccion antifalsificacion y alcanza el servicio genera exactamente un registro; las solicitudes detenidas antes del servicio no generan auditoria y, si el elemento no puede resolverse, solo se conserva una referencia no reversible.
- Q: ¿Que protocolo debe usarse para determinar que al menos el 95% de las operaciones administrativas termina en menos de dos segundos? → A: Ejecutar 20 solicitudes de calentamiento y luego medir 200 solicitudes validas, 50 por cada tipo de operacion, en un entorno equivalente a produccion y sin incluir latencia de red publica.
- Q: ¿Que debe prevalecer cuando se repite un cambio de estado con una revision que quedo obsoleta por la primera solicitud? → A: Validar primero la revision; una repeticion con token obsoleto devuelve conflicto sin mutar ni publicar, aunque el estado solicitado ya coincida.
- Q: ¿Que formato debe aceptar la fuente editorial requerida al publicar? → A: Texto libre no vacio de hasta 500 caracteres despues de ignorar espacios exteriores; puede ser una URL o una referencia documental interna.
- Q: ¿Que muestra manual debe usarse para validar el flujo administrativo con un equipo de cinco personas? → A: Tres integrantes del equipo, cada uno con una cuenta administrativa desechable; los tres deben completar el flujo e identificar estado y orden, y dos deben provocar una colision controlada que el tercero verifica antes del reintento.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Administrar tracks (Priority: P1)

Como administrador de contenido, quiero crear, editar, ordenar, activar y desactivar tracks para mantener un catalogo de rutas de aprendizaje organizado y vigente.

**Why this priority**: Los tracks son la estructura principal del catalogo; sin ellos no se pueden agrupar modulos ni ofrecer rutas de aprendizaje.

**Independent Test**: Un administrador de contenido puede crear dos tracks con sus datos obligatorios, editar sus datos, cambiar su orden y estado, y comprobar que los cambios quedan conservados.

**Acceptance Scenarios**:

1. **Given** un administrador de contenido autenticado, **When** crea un track con titulo, descripcion y audiencia validos, **Then** el sistema conserva el track en estado inactivo y le asigna una posicion visible en el catalogo administrativo.
2. **Given** un track existente, **When** un administrador de contenido modifica su titulo, descripcion o audiencia con valores validos, **Then** el sistema conserva los nuevos datos sin alterar sus modulos ni su posicion.
3. **Given** varios tracks existentes, **When** un administrador de contenido cambia el orden de uno de ellos, **Then** el catalogo administrativo y la vista del aprendiz conservan el nuevo orden sin posiciones duplicadas ni huecos.
4. **Given** un track activo, **When** un administrador de contenido lo desactiva, **Then** el track y todos sus modulos dejan de estar disponibles para aprendices sin ser eliminados.
5. **Given** un track inactivo que cumple las condiciones editoriales, **When** un administrador de contenido lo activa, **Then** el track queda disponible para aprendices en su posicion definida y conserva una version publicada trazable.

---

### User Story 2 - Administrar modulos de un track (Priority: P2)

Como administrador de contenido, quiero crear, editar, ordenar, activar y desactivar modulos dentro de un track para definir una secuencia de aprendizaje clara.

**Why this priority**: Los modulos convierten un track en una ruta recorrible y su posicion determina la secuencia que sigue el aprendiz.

**Independent Test**: Dentro de un track existente, un administrador de contenido puede crear tres modulos, editar sus datos, reordenarlos y cambiar su estado; la secuencia resultante conserva posiciones consecutivas y solo muestra los modulos activos.

**Acceptance Scenarios**:

1. **Given** un track existente, **When** un administrador de contenido crea un modulo con titulo y objetivo validos, **Then** el sistema lo conserva en estado inactivo en la ultima posicion del track.
2. **Given** un modulo existente, **When** un administrador de contenido modifica su titulo u objetivo con valores validos, **Then** el sistema conserva los nuevos datos sin cambiar su track ni su posicion.
3. **Given** varios modulos en un track, **When** un administrador de contenido mueve un modulo a otra posicion valida, **Then** todos los modulos del track quedan en una secuencia unica, consecutiva y persistente.
4. **Given** un modulo activo, **When** un administrador de contenido lo desactiva, **Then** deja de estar disponible para aprendices y los demas modulos conservan su orden relativo.
5. **Given** un modulo inactivo que cumple las condiciones editoriales, **When** un administrador de contenido lo activa, **Then** queda disponible para aprendices si su track tambien esta activo y conserva una version publicada trazable.

---

### User Story 3 - Explorar una ruta activa de forma segura (Priority: P3)

Como aprendiz, quiero ver los tracks y modulos activos en el orden definido para elegir y recorrer rutas vigentes sin acceder a herramientas administrativas.

**Why this priority**: La administracion de contenido solo aporta valor cuando produce un catalogo seguro, coherente y comprensible para el aprendiz.

**Independent Test**: Con una combinacion de tracks y modulos activos e inactivos, un aprendiz autenticado ve unicamente el contenido activo bajo tracks activos, en el orden definido, y todos sus intentos de abrir o ejecutar acciones administrativas son denegados.

**Acceptance Scenarios**:

1. **Given** tracks activos e inactivos, **When** un aprendiz consulta el catalogo, **Then** ve exclusivamente los tracks activos ordenados por la posicion definida por administracion.
2. **Given** un track activo con modulos activos e inactivos, **When** un aprendiz consulta el track, **Then** ve exclusivamente sus modulos activos en orden ascendente de posicion.
3. **Given** un track inactivo con modulos activos, **When** un aprendiz consulta el catalogo o intenta abrir directamente ese track o uno de sus modulos, **Then** no recibe el contenido inactivo ni informacion editorial privada.
4. **Given** un aprendiz autenticado, **When** intenta consultar o ejecutar cualquier accion administrativa sobre tracks o modulos, **Then** la operacion se deniega y ningun dato cambia.

### Edge Cases

- Un track o modulo con titulo vacio, compuesto solo por espacios o por encima del limite comunicado se rechaza sin crear ni modificar un registro parcial.
- Crear o editar un track con un titulo equivalente al de otro track, o un modulo con un titulo equivalente al de otro modulo del mismo track, se rechaza despues de ignorar mayusculas y espacios exteriores; el mismo titulo de modulo puede usarse en tracks distintos.
- Un track no puede activarse si no tiene al menos un modulo activo; el sistema explica al administrador que debe completar la ruta antes de publicarla.
- Un modulo puede activarse mientras su track esta inactivo, pero permanece invisible e inaccesible para aprendices hasta que el track tambien este activo.
- Desactivar un track no cambia el estado propio de sus modulos; al reactivarlo, vuelven a ser visibles solo los modulos que continuen activos.
- Mover un track o modulo a la primera o ultima posicion reajusta el resto de la secuencia sin duplicados ni huecos.
- Una posicion solicitada fuera de la secuencia valida se rechaza sin cambiar el orden existente y se informa el rango permitido.
- Cuando dos administradores parten de la misma version, el primer cambio valido se acepta y cualquier edicion o reordenamiento posterior basado en esa version obsoleta se rechaza sin sobrescribir datos; el segundo administrador debe recargar antes de reintentar.
- Un acceso de aprendiz a un identificador inexistente o inactivo recibe una respuesta que no revela datos editoriales ni permite distinguir el estado interno del contenido.
- Desactivar contenido que un aprendiz tenia abierto impide obtenerlo de nuevo en la siguiente solicitud, sin eliminar historial de aprendizaje previo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Solo una cuenta autenticada con rol de administrador de contenido DEBE poder acceder a las acciones administrativas de tracks y modulos.
- **FR-002**: El sistema DEBE permitir que un administrador de contenido cree un track con titulo, descripcion y audiencia obligatorios, estado inicial inactivo y una posicion unica dentro del catalogo.
- **FR-003**: El sistema DEBE permitir que un administrador de contenido edite el titulo, descripcion y audiencia de un track existente sin eliminarlo ni desvincular sus modulos.
- **FR-004**: El sistema DEBE permitir que un administrador de contenido ordene todos los tracks mediante posiciones unicas y consecutivas, y DEBE conservar ese orden para consultas posteriores.
- **FR-005**: El sistema DEBE permitir que un administrador de contenido active o desactive un track sin eliminarlo; un track solo DEBE poder activarse cuando contiene al menos un modulo activo y cumple las condiciones editoriales de publicacion.
- **FR-006**: El sistema DEBE permitir que un administrador de contenido cree un modulo dentro de un unico track con titulo y objetivo obligatorios, estado inicial inactivo y la ultima posicion disponible de ese track.
- **FR-007**: El sistema DEBE permitir que un administrador de contenido edite el titulo y objetivo de un modulo existente sin cambiar automaticamente el track, la posicion ni el estado del modulo.
- **FR-008**: El sistema DEBE permitir que un administrador de contenido mueva un modulo a una posicion valida dentro de su track y DEBE reajustar los demas modulos para mantener posiciones unicas y consecutivas desde uno.
- **FR-009**: El sistema DEBE permitir que un administrador de contenido active o desactive un modulo sin eliminarlo y sin cambiar el orden relativo de los demas modulos.
- **FR-010**: El sistema DEBE mostrar a los aprendices solamente tracks activos, ordenados por su posicion administrativa.
- **FR-011**: Dentro de un track activo, el sistema DEBE mostrar a los aprendices solamente modulos activos, ordenados de forma ascendente por posicion.
- **FR-012**: El sistema NO DEBE mostrar ni entregar a un aprendiz un track inactivo, un modulo inactivo o cualquier modulo cuyo track este inactivo, incluso mediante acceso directo.
- **FR-013**: Todo intento de un aprendiz de consultar o ejecutar una accion administrativa DEBE ser denegado, no DEBE modificar datos y no DEBE revelar informacion editorial privada.
- **FR-014**: El sistema DEBE validar los datos obligatorios y los cambios de posicion antes de conservarlos; una operacion invalida DEBE dejar los datos y el orden previos sin cambios y explicar el error al administrador.
- **FR-015**: Cada primera activacion de un track o modulo, cada transicion posterior de inactivo a activo aunque el contenido no haya cambiado y cada edicion aceptada mientras el elemento permanece activo DEBE conservar una nueva version publicada inmutable con autor, fuente, numero de version, fecha de revision y estado editorial. Repetir una activacion mientras el elemento ya esta activo DEBE ser idempotente y NO DEBE crear otra version. Antes de guardar una edicion de un elemento activo, el administrador DEBE confirmar la fuente, la fecha de revision y el estado editorial; el sistema DEBE asignar automaticamente como autor al administrador autenticado y el siguiente numero de version. La fuente DEBE ser un texto no vacio de hasta 500 caracteres despues de ignorar espacios exteriores y PUEDE contener una URL o una referencia documental interna sin exigir un formato URL. Cada elemento DEBE tener su propia secuencia de versiones, comenzando en 1 e incrementando exactamente en uno con cada publicacion. Editar un elemento inactivo NO DEBE publicarlo, y ninguna operacion DEBE alterar una version historica.
- **FR-016**: Cada solicitud de cambio autenticada que supera las protecciones previas de seguridad y alcanza el servicio para crear, editar, activar, desactivar o reordenar tracks o modulos DEBE generar exactamente un registro con actor, accion, resultado y fecha. El registro DEBE identificar el elemento cuando pueda resolverse; si la referencia es inexistente o malformada, DEBE conservar solo una referencia no reversible que permita correlacionar intentos repetidos sin almacenar ni revelar el valor solicitado. Las solicitudes anonimas o rechazadas por las protecciones previas DEBEN detenerse antes del servicio y NO DEBEN generar este registro.
- **FR-017**: La desactivacion de un track o modulo NO DEBE eliminar el elemento, sus versiones publicadas ni las referencias historicas de aprendizaje asociadas.
- **FR-018**: El sistema DEBE rechazar toda edicion, reordenamiento o cambio de estado basado en una revision que dejo de ser vigente, conservar sin cambios el resultado aceptado previamente e indicar al administrador que recargue el estado actual antes de reintentar. La revision esperada DEBE validarse antes de comprobar si el estado solicitado ya coincide: una repeticion con revision obsoleta produce conflicto sin mutacion ni nueva version; solo una solicitud con revision vigente puede completarse como exito sin cambios.
- **FR-019**: El sistema DEBE exigir que cada titulo de track sea unico en el catalogo y que cada titulo de modulo sea unico dentro de su track, comparandolos sin distinguir mayusculas y despues de ignorar espacios exteriores; DEBE permitir el mismo titulo de modulo en tracks distintos.

### Acceptance Criteria by Requirement

- **AC-FR-001/013**: Una cuenta con rol de administrador de contenido puede abrir y ejecutar las acciones administrativas; los mismos intentos de una cuenta aprendiz son denegados, no cambian datos y no exponen campos editoriales.
- **AC-FR-002/003**: Un track creado con datos validos queda inactivo al final del catalogo; editarlo cambia solo los campos enviados y conserva sus modulos y posicion. Datos obligatorios invalidos no crean ni modifican el track.
- **AC-FR-004/014**: Mover un track a cada extremo y a una posicion intermedia produce una secuencia completa desde uno; una posicion invalida conserva exactamente el orden anterior y muestra el rango permitido.
- **AC-FR-005**: Un track con al menos un modulo activo y metadatos editoriales completos puede activarse y desactivarse; un track sin modulos activos no puede activarse y permanece inactivo.
- **AC-FR-006/007**: Un modulo creado con datos validos pertenece a un solo track, queda inactivo al final de su secuencia y puede editar titulo u objetivo sin cambiar automaticamente su relacion, posicion o estado.
- **AC-FR-008/014**: Mover un modulo dentro de su track reajusta la secuencia completa desde uno sin duplicados ni huecos; una posicion fuera del rango conserva exactamente el orden previo.
- **AC-FR-009**: Activar o desactivar un modulo cambia solo su estado y mantiene el orden relativo de todos los modulos del track.
- **AC-FR-010/011/012**: Una matriz de prueba con tracks y modulos activos e inactivos muestra al aprendiz solo tracks activos y, dentro de ellos, solo modulos activos en el orden definido; todos los accesos directos al contenido no visible son denegados sin revelar sus datos.
- **AC-FR-015**: Activar por primera vez un elemento genera su version 1 con los cinco datos de trazabilidad; cada reactivacion desde estado inactivo genera la siguiente version aunque el contenido no haya cambiado, mientras repetir la activacion estando ya activo no crea una version. Editarlo mientras esta activo exige confirmar una fuente no vacia de hasta 500 caracteres, una fecha de revision y el estado editorial antes de guardar, asigna automaticamente el administrador autenticado como autor y genera una nueva version publicada; tanto una URL como una referencia documental interna son fuentes validas. Omitir una confirmacion o superar el limite rechaza el cambio sin alterar la version vigente. Editarlo mientras esta inactivo no lo publica hasta su activacion. En todos los casos, las versiones anteriores permanecen sin cambios y la secuencia de otro elemento no se altera.
- **AC-FR-016**: Cada solicitud administrativa de cambio iniciada por una cuenta autenticada que supera las protecciones previas y alcanza el servicio genera exactamente un registro con actor, accion, resultado y fecha, tanto si se completa como si se rechaza. Los elementos resueltos quedan identificados directamente; referencias inexistentes o malformadas conservan solo un valor no reversible distinto del texto solicitado. Las solicitudes anonimas o detenidas por protecciones previas no generan registros de dominio.
- **AC-FR-017**: Tras desactivar un elemento con versiones o referencias historicas, deja de estar disponible para nuevas consultas del aprendiz pero todas las versiones y referencias previas siguen consultables por los procesos autorizados.
- **AC-FR-018**: Cuando dos administradores cargan la misma revision, el primer cambio valido se conserva; una edicion, reordenamiento o cambio de estado posterior basado en la revision obsoleta se rechaza, no altera el estado ni las versiones aceptadas y solicita recargar antes de reintentar. Repetir un cambio de estado con la revision obsoleta produce el mismo conflicto aunque el estado solicitado ya coincida; con revision vigente, solicitar el estado actual es un exito sin cambios.
- **AC-FR-019**: Crear o editar un track con un titulo equivalente al de otro track se rechaza; crear o editar un modulo con un titulo equivalente al de otro modulo del mismo track se rechaza; el mismo titulo de modulo en dos tracks distintos se acepta. Las variantes de mayusculas o espacios exteriores producen el mismo resultado.

### Key Entities *(include if feature involves data)*

- **Track**: Ruta de aprendizaje que agrupa modulos. Registra un titulo unico en el catalogo, descripcion, audiencia, estado y posicion; conserva sus versiones publicadas y su historial administrativo.
- **Modulo**: Unidad ordenada dentro de un unico track. Registra un titulo unico dentro de ese track, objetivo, posicion y estado; conserva sus versiones publicadas y su historial administrativo. Un titulo puede repetirse en tracks distintos.
- **Version publicada**: Instantanea inmutable de un track o modulo activado; registra autor, fuente, numero de version, fecha de revision y estado editorial para mantener trazabilidad del contenido presentado. Su numero pertenece a la secuencia del elemento, empieza en 1 y aumenta en uno con cada nueva publicacion.
- **Registro administrativo**: Evidencia de una creacion, edicion, activacion, desactivacion o reordenamiento que alcanzo el servicio; identifica actor, accion, resultado y fecha. Relaciona el elemento cuando existe o una referencia solicitada no reversible cuando no puede resolverse, nunca ambos ni el valor crudo.
- **Administrador de contenido**: Cuenta autorizada para gestionar tracks y modulos, pero sin autoridad implicita para administrar roles de otras cuentas.
- **Aprendiz**: Cuenta que puede explorar contenido activo en el orden publicado y no puede acceder a las acciones ni a los datos editoriales de administracion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una prueba manual interna con tres administradores de contenido del equipo, los tres crean un track con tres modulos, los ordenan y dejan la ruta lista para aprendices en menos de 5 minutos y sin asistencia.
- **SC-002**: El 100% de las secuencias de prueba de tracks y modulos conserva posiciones unicas y consecutivas despues de creaciones y reordenamientos validos.
- **SC-003**: El 100% de las consultas de prueba de aprendices muestra solo tracks activos y modulos activos bajo tracks activos, respetando el orden definido.
- **SC-004**: El 100% de los intentos de prueba de aprendices sobre acciones administrativas son denegados sin cambios de datos ni exposicion de informacion editorial privada.
- **SC-005**: El 100% de las activaciones de prueba conserva una version publicada completa y el 100% de las ediciones posteriores deja inmutables las versiones anteriores.
- **SC-006**: En la misma prueba de aceptacion de SC-001, los tres participantes identifican sin asistencia el estado activo o inactivo de cada track y modulo y el orden que vera el aprendiz. Ademas, dos participantes envian cambios desde la misma revision: el primero se conserva, el segundo recibe conflicto sin sobrescritura y puede recargar y reintentar; el tercero verifica el estado final.
- **SC-007**: El 100% de las desactivaciones de prueba oculta el elemento para nuevas consultas de aprendices sin eliminar sus versiones ni referencias historicas.
- **SC-008**: En un catalogo con 100 tracks y 50 modulos por track, despues de excluir 20 solicitudes de calentamiento, al menos el 95% de una muestra medida de 200 solicitudes administrativas validas DEBE completar su respuesta del sistema en menos de 2 segundos. La muestra DEBE contener 50 solicitudes de creacion, 50 de edicion, 50 de reordenamiento y 50 de cambio de estado, ejecutarse en un entorno con configuracion y almacenamiento equivalentes a produccion y excluir la latencia de red publica. La evidencia DEBE registrar la configuracion y capacidad del entorno, el numero de observaciones y el percentil obtenido.

## Assumptions

- La posicion de tracks forma parte del orden visible del catalogo aunque los criterios iniciales solo enumeren titulo, descripcion, audiencia y estado como datos editoriales del track.
- Los tracks y modulos se crean inactivos para evitar publicar contenido incompleto; activar equivale a publicar la version vigente, editar un elemento activo publica una nueva version y desactivar equivale a retirarlo de nuevas consultas de aprendices.
- Los estados necesarios para este alcance son activo e inactivo. Flujos editoriales adicionales, como borrador, en revision o archivado, quedan fuera de esta feature.
- Un track requiere al menos un modulo activo para activarse; un modulo puede prepararse y activarse antes que su track sin quedar visible para aprendices.
- La audiencia es una descripcion editorial de las personas destinatarias y no aplica segmentacion automatica ni restricciones adicionales de acceso en esta feature.
- La fuente, fecha de revision y estado editorial se proporcionan o confirman durante cada activacion y antes de guardar una edicion de contenido activo; la fuente admite una URL o referencia documental interna en texto libre no vacio hasta 500 caracteres, y el autor autenticado y el numero de version se asignan automaticamente.
- La autenticacion y los roles de aprendiz y administrador de contenido ya existen y se reutilizan; la asignacion de roles no forma parte de esta feature.
- Los limites de longitud de textos se comunicaran de forma consistente al administrador y se concretaran durante la planificacion sin cambiar los campos obligatorios.
- La eliminacion permanente, el traslado de un modulo entre tracks y el ordenamiento condicionado por audiencia quedan fuera de alcance.

## Scope Boundaries

### In Scope

- Crear, editar, ordenar, activar y desactivar tracks.
- Crear, editar, ordenar, activar y desactivar modulos dentro de un track.
- Mostrar a aprendices solo la jerarquia activa en el orden administrativo.
- Proteger todas las acciones administrativas por rol.
- Conservar versiones publicadas e historial administrativo de tracks y modulos.

### Out of Scope

- Eliminar permanentemente tracks o modulos.
- Mover modulos de un track a otro.
- Crear microlecciones, evaluaciones u otros contenidos internos de un modulo.
- Inscripcion, progreso, puntuacion o recomendaciones personalizadas del aprendiz.
- Crear o asignar cuentas y roles administrativos.
- Segmentar automaticamente el catalogo segun el campo audiencia.

## Dependencies

- La feature de autenticacion y perfil debe proporcionar sesiones validas y los roles de aprendiz y administrador de contenido.
- Los procesos posteriores de exploracion y aprendizaje consumiran el catalogo activo y deben respetar sus estados, orden y versiones publicadas.
