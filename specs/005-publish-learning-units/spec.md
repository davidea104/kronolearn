# Feature Specification: Publicacion de unidades de aprendizaje

**Feature Branch**: `005-publish-learning-units`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Como administrador de contenido quiero que las unidades de aprendizaje de los dos tracks queden publicadas y versionadas, para que los aprendices tengan que estudiar desde el primer dia. El track principal debe contener siete unidades y el secundario tres, con contenido trazable, versiones congeladas y una carga repetible sin duplicados."

## Clarifications

### Session 2026-08-22

- Q: Si el modulo de destino ya contiene unidades adicionales que no pertenecen a la carga controlada, ¿que debe hacer la carga para mantener el requisito de exactamente siete y tres unidades? → A: Rechazar la carga completa e informar el conflicto.
- Q: ¿Que resultado debe garantizarse cuando dos ejecuciones de la carga de contenido comienzan al mismo tiempo? → A: Ambas terminan correctamente con un unico estado, sin duplicados.
- Q: Si una posicion esperada de una unidad controlada esta ocupada por contenido que no puede reconocerse como parte de la carga controlada, ¿que debe hacer la carga? → A: Rechazar la carga completa e informar la colision.
- Q: ¿Cuantas opciones debe contener cada una de las diez unidades publicadas? → A: Tres o cuatro segun la unidad, definidas en el contenido aprobado.
- Q: ¿Donde debe residir el corpus aprobado para que pueda actualizarse sin modificar el codigo fuente de la aplicacion? → A: En un archivo JSON versionado bajo `catalog/content_data/`, separado del codigo ejecutable y validado antes de persistir.
- Q: ¿Como debe conservar cada `ContentVersion` su estado editorial de forma explicita? → A: Mediante un campo inmutable `editorial_status` con valor `published`; esta feature incluye la migracion de catalogo indispensable.
- Q: ¿Como debe obtener `catalog` la cuenta autora sin consultar directamente el modelo de `accounts`? → A: Mediante un servicio publico de consulta en `accounts/services/queries.py`, probado bajo `tests/accounts/`, que resuelve y bloquea la cuenta y devuelve un resultado autorizado o generico.
- Q: ¿De donde debe obtener el comando la identidad autora durante un despliegue no interactivo? → A: De una cuenta de despliegue preexistente identificada mediante configuracion privada del servidor; el comando no acepta `--actor-id` y la constitucion debe reconocer este contexto confiable para procesos no interactivos.
- Q: ¿Cual debe ser el titulo canonico del track secundario? → A: `Fundamentos de negocio para equipos técnicos`; la variante sin tilde se reconoce temporalmente solo como alias legacy y nunca como una identidad adicional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publicar el catalogo inicial completo (Priority: P1)

Como administrador de contenido, quiero cargar y publicar las unidades previstas para los dos tracks para que el catalogo de aprendizaje este completo desde el primer dia.

**Why this priority**: Sin las diez unidades vigentes, los aprendices no disponen del recorrido formativo comprometido y los tracks publicados quedan incompletos.

**Independent Test**: Partiendo de una instalacion desplegada, se ejecuta la carga controlada de contenido y se comprueba que crea o reconoce los dos tracks y sus modulos, deja el principal publicado con siete unidades ordenadas, el secundario con tres y cada unidad con todos sus componentes y metadatos obligatorios.

**Acceptance Scenarios**:

1. **Given** una instalacion desplegada y una cuenta administradora de contenido autorizada, **When** se ejecuta el comando de carga de contenido, **Then** crea o reconoce los tracks "Crea tu registro de gastos con agentes y SDD" y "Fundamentos de negocio para equipos técnicos" y su modulo correspondiente, y ambos tracks quedan publicados con siete y tres unidades vigentes respectivamente.
2. **Given** el track principal publicado, **When** se revisan sus unidades en orden, **Then** recorren problema, usuario y alcance minimo; historias y criterios verificables; especificacion; plan y tareas; implementacion; pruebas, privacidad y seguridad; y despliegue, verificacion y evaluacion.
3. **Given** el track secundario publicado, **When** se revisan sus unidades en orden, **Then** cubren problema y propuesta de valor; costos, ingresos y priorizacion; y riesgo y comunicacion con areas no tecnicas.
4. **Given** una unidad de cualquiera de los tracks, **When** se inspecciona su version vigente, **Then** contiene titulo, objetivo de aprendizaje, microleccion, caso con datos ficticios, entre tres y cuatro opciones ordenadas, consecuencia y explicacion para cada opcion, al menos una opcion optima, fuente, autor, fecha de revision y estado editorial `published`, y su contenido esta dimensionado para completarse en cinco minutos o menos.
5. **Given** las siete unidades del track principal y las tres del secundario, **When** se revisan sus actividades, **Then** cada unidad principal tiene un laboratorio y ninguna unidad secundaria tiene laboratorio.
6. **Given** que la carga ya termino correctamente, **When** se ejecuta de nuevo con el mismo contenido, **Then** se conservan exactamente las mismas identidades, versiones vigentes, valores, relaciones, orden y cantidades, sin duplicados ni nuevas versiones.

---

### User Story 2 - Impedir publicaciones incompletas (Priority: P2)

Como administrador de contenido, quiero que la publicacion rechace unidades pedagogica o editorialmente incompletas para que ningun aprendiz reciba contenido sin decisiones validas o sin trazabilidad.

**Why this priority**: Las opciones y los metadatos editoriales son necesarios para ofrecer una decision evaluable y para conocer la procedencia y vigencia del contenido.

**Independent Test**: Se intenta publicar una unidad variando por separado la cantidad de opciones, la existencia de una opcion optima, la fuente, el autor y la fecha de revision; solo el conjunto completamente valido puede publicarse.

**Acceptance Scenarios**:

1. **Given** una unidad en preparacion con menos de tres o mas de cuatro opciones, **When** se solicita su publicacion, **Then** la solicitud se rechaza y no queda una nueva version publicada.
2. **Given** una unidad en preparacion con tres o cuatro opciones pero ninguna optima, **When** se solicita su publicacion, **Then** la solicitud se rechaza y no queda una nueva version publicada.
3. **Given** una unidad en preparacion sin fuente, sin autor o sin fecha de revision, **When** se solicita su publicacion, **Then** la solicitud se rechaza, se identifican los datos faltantes y no queda una version parcial.
4. **Given** una unidad completa y valida, **When** se solicita su publicacion, **Then** se crea una unica version vigente con todos sus componentes asociados.

---

### User Story 3 - Conservar versiones publicadas (Priority: P3)

Como responsable del catalogo, quiero que cada version publicada permanezca congelada para que el contenido presentado a los aprendices sea trazable y no cambie retroactivamente.

**Why this priority**: La inmutabilidad permite explicar exactamente que estudio y decidio cada aprendiz, incluso despues de que el contenido evolucione.

**Independent Test**: Se publica una unidad y luego se intentan modificar o eliminar su texto, metadatos, opciones y laboratorio; todos los intentos se rechazan y la version conserva exactamente su estado original.

**Acceptance Scenarios**:

1. **Given** una version publicada, **When** cualquier operacion posterior intenta cambiar sus textos, metadatos editoriales o fecha de publicacion, **Then** la operacion se rechaza y la version permanece identica.
2. **Given** una version publicada, **When** cualquier operacion posterior intenta agregar, quitar, reordenar o modificar sus opciones o laboratorio, **Then** la operacion se rechaza y el conjunto publicado permanece identico.
3. **Given** una unidad que necesita correccion, **When** se publica contenido revisado valido, **Then** se crea una version posterior y la version anterior permanece congelada y disponible para trazabilidad.

---

### User Story 4 - Estudiar desde el primer dia (Priority: P4)

Como aprendiz, quiero encontrar los dos tracks publicados con sus unidades completas para comenzar el recorrido que me corresponde sin depender de una carga manual posterior.

**Why this priority**: El valor final de la carga es que el contenido vigente este realmente disponible para aprendizaje desde la puesta en marcha.

**Independent Test**: Un aprendiz consulta ambos tracks despues de la carga y puede recorrer las diez unidades vigentes en el orden definido, viendo unicamente datos ficticios y los componentes pedagogicos correspondientes.

**Acceptance Scenarios**:

1. **Given** un aprendiz con acceso al catalogo, **When** abre el track principal publicado, **Then** encuentra sus siete unidades vigentes en el orden del ciclo definido.
2. **Given** un aprendiz con acceso al catalogo, **When** abre el track secundario publicado, **Then** encuentra sus tres unidades vigentes en el orden definido.
3. **Given** una unidad publicada de cualquiera de los tracks, **When** el aprendiz la estudia, **Then** puede leer la microleccion y el caso, elegir entre tres o cuatro opciones y recibir la consecuencia y explicacion asociadas sin encontrar datos personales reales.

### Edge Cases

- Una opcion vacia, repetida dentro de la misma version o sin consecuencia o explicacion deja la unidad incompleta y bloquea su publicacion.
- Las posiciones de las opciones deben formar una secuencia unica y consecutiva; una posicion duplicada o un hueco bloquea la publicacion.
- Una fuente, un autor o una fecha de revision vacios no se consideran metadatos presentes; una fecha futura tampoco se acepta como revision ya realizada.
- Un fallo durante la carga no puede dejar uno de los tracks o una unidad parcialmente publicados; el estado previo completo debe conservarse.
- Si ya existen las dos unidades demo iniciales en la primera posicion de sus respectivos modulos, la carga debe reconocer esas ubicaciones como identidades estables y llevar el catalogo a diez unidades vigentes sin convertirlas en unidades adicionales.
- Si una unidad controlada por la carga existe incompleta y aun no tiene una version publicada, la carga puede completarla; si ya tiene una version publicada distinta, debe conservarla y publicar una unica version posterior que coincida con la definicion esperada.
- Si un modulo de destino contiene una unidad adicional que no pertenece a la definicion controlada, la carga completa se rechaza, informa el conflicto y conserva todo el estado previo sin retirar ni sobrescribir la unidad ajena.
- Si una posicion esperada esta ocupada por contenido que no puede reconocerse como parte de la definicion controlada, la carga completa se rechaza, informa la colision y no convierte, mueve, reversiona ni sobrescribe el contenido existente.
- Si dos ejecuciones de la carga comienzan al mismo tiempo sobre un estado compatible, ambas deben terminar correctamente y observar el mismo estado final completo, sin unidades, versiones ni componentes duplicados.
- Repetir la carga despues de alcanzar el estado esperado no puede cambiar fechas de publicacion, numeros de version ni ningun otro dato.
- Una unidad del track principal sin laboratorio o una del secundario con laboratorio no satisface el conjunto de contenido esperado.
- Los nombres de personas, comercios, cuentas, montos y situaciones incluidos en microlecciones, casos, opciones y laboratorios deben ser ficticios y no corresponder a personas identificables.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE proporcionar un unico comando de despliegue, sin argumento de identidad de cuenta, para crear o reconciliar los tracks "Crea tu registro de gastos con agentes y SDD" y "Fundamentos de negocio para equipos técnicos", sus modulos y su contenido inicial completo a partir de un archivo JSON versionado bajo `catalog/content_data/`, separado del codigo ejecutable y validado por completo antes de la primera escritura. El comando de demostracion creado por la feature 004 permanece separado y sin modificaciones.
- **FR-002**: Dentro del modulo publicado del track principal DEBEN existir exactamente siete unidades vigentes y ordenadas cuyos temas sean, en este orden: problema, usuario y alcance minimo; historias de usuario y criterios verificables; especificacion de datos, comportamiento y restricciones; plan y tareas pequenas para el agente; implementacion de registro, listado y persistencia de gastos; pruebas, privacidad y seguridad; y despliegue, verificacion y evaluacion.
- **FR-003**: Dentro del modulo publicado del track secundario DEBEN existir exactamente tres unidades vigentes y ordenadas cuyos temas sean, en este orden: problema y propuesta de valor; costos, ingresos y priorizacion; y riesgo y comunicacion con areas no tecnicas.
- **FR-004**: Cada version publicada DEBE conservar explicitamente titulo, objetivo de aprendizaje, microleccion, caso, fuente, autor, fecha de revision, fecha de publicacion y el estado editorial inmutable `published`, y DEBE estar dimensionada editorialmente para que un aprendiz de la audiencia objetivo la complete en cinco minutos o menos.
- **FR-005**: Cada version publicada DEBE contener tres o cuatro opciones segun el conteo fijado para esa unidad en la definicion de contenido aprobada, con posiciones unicas y consecutivas; cada opcion DEBE contener texto, valoracion pedagogica, consecuencia y explicacion, y al menos una opcion DEBE estar valorada como optima. La carga NO DEBE elegir el conteo durante la ejecucion ni variarlo entre repeticiones de una misma definicion.
- **FR-006**: La publicacion DEBE rechazarse sin crear una version parcial cuando la unidad tenga menos de tres o mas de cuatro opciones, ninguna opcion optima, posiciones invalidas, una opcion incompleta o cualquiera de los metadatos fuente, autor o fecha de revision ausente o invalido.
- **FR-007**: Cada una de las siete unidades del track principal DEBE incluir exactamente un laboratorio con objetivo, consigna inicial, artefacto esperado y una lista con al menos un paso de verificacion; todos esos componentes DEBEN ser no vacios. Las tres unidades del track secundario NO DEBEN incluir laboratorio.
- **FR-008**: Todo dato narrativo o contextual de las unidades, incluidas microlecciones, casos, opciones y laboratorios, DEBE ser ficticio y no identificar a una persona real.
- **FR-009**: Cada publicacion valida DEBE crear una nueva version numerada y vigente de la unidad sin modificar ninguna version publicada previamente.
- **FR-010**: Una version publicada y sus opciones y laboratorio asociados NO DEBEN poder modificarse ni eliminarse mediante ninguna operacion posterior.
- **FR-011**: Cuando se publique una correccion valida, el sistema DEBE conservar la version anterior sin cambios, crear la siguiente version para esa unidad y hacer vigente unicamente la nueva version.
- **FR-012**: La carga DEBE reconocer cada track por su titulo estable, su modulo por el titulo dentro del track, cada unidad controlada por su posicion dentro de ese modulo, cada opcion por su posicion dentro de la version y el laboratorio por su relacion unica con la version. El titulo canonico del track secundario es "Fundamentos de negocio para equipos técnicos"; la variante "Fundamentos de negocio para equipos tecnicos" solo puede reconocerse como alias legacy durante la reconciliacion y NO DEBE crear ni conservar una identidad adicional. Una posicion solo identifica una unidad controlada cuando el contenido existente puede reconocerse como perteneciente a la definicion; los titulos y textos de una version publicada NO DEBEN usarse por si solos para convertir contenido ajeno ni para modificar una instantanea.
- **FR-013**: Despues de que una ejecucion alcance la definicion esperada, toda ejecucion consecutiva con esa misma definicion DEBE producir exactamente el mismo estado logico: iguales identidades, valores, relaciones, posiciones, cantidades, numeros de version y versiones vigentes, sin crear ni modificar registros.
- **FR-014**: La carga DEBE reconocer como parte del conjunto objetivo las unidades demo iniciales ubicadas en la primera posicion de cada modulo y ampliar el catalogo hasta diez unidades sin duplicarlas. Si su version vigente difiere del contenido esperado, DEBE conservarla congelada y publicar una sola version posterior valida; una repeticion con la misma definicion se rige por FR-013 y no crea otra version.
- **FR-015**: La carga DEBE completarse como una sola operacion logica: si alguna unidad o relacion no puede validarse o publicarse, si un modulo de destino contiene una unidad adicional ajena a la definicion controlada o si una posicion esperada esta ocupada por contenido no reconocible como controlado, la ejecucion completa DEBE rechazarse, informar el conflicto o la colision y conservar todo el estado previo sin convertir, mover, reversionar, retirar ni sobrescribir contenido.
- **FR-016**: Al terminar correctamente la carga, un aprendiz con acceso al catalogo DEBE poder consultar las diez unidades vigentes en el orden definido y recibir los componentes pedagogicos de la version exacta presentada.
- **FR-017**: Esta especificacion DEBE observar los principios 3, 6, 10, 12, 13, 14 y 16 de la constitucion vigente sobre contenido administrado como datos, verificacion obligatoria, contenido trazable y versionado, autorizacion, privacidad, comunicacion entre modulos y propiedad de archivos. La cuenta autora DEBE proceder de la configuracion privada del servidor para el proceso de despliegue, y DEBE resolverse, bloquearse y autorizarse mediante un servicio publico del modulo `accounts`; `catalog` NO DEBE importar ni consultar directamente el modelo de cuenta ni aceptar su identificador como argumento del comando.
- **FR-018**: Dos ejecuciones de la carga que comiencen simultaneamente sobre un estado compatible DEBEN terminar correctamente, devolver resultados equivalentes y converger en un unico estado final completo, sin duplicar tracks, modulos, unidades, versiones, opciones ni laboratorios.

### Acceptance Criteria by Requirement

- **AC-FR-001-003**: Una carga mediante el comando de despliegue deja ambos tracks y sus modulos publicados, con exactamente siete y tres unidades vigentes respectivamente; una comparacion por posicion de modulo y luego por posicion de unidad confirma los diez temas en el orden indicado, y el comando de demostracion de 004 permanece sin modificaciones.
- **AC-FR-004-006**: Una matriz que omite por separado cada campo obligatorio, prueba dos, tres, cuatro y cinco opciones, elimina todas las opciones optimas, rompe posiciones y deja incompleta cada parte de una opcion confirma que solo las unidades plenamente validas se publican y que todos los rechazos dejan cero versiones parciales. Las diez versiones vigentes conservan explicitamente el estado editorial `published`; para las diez unidades de despliegue, cada conteo de tres o cuatro coincide exactamente con su definicion aprobada y se conserva en cada repeticion de la carga.
- **AC-FR-007**: La inspeccion de las diez versiones vigentes encuentra exactamente siete laboratorios, uno por cada unidad principal y ninguno en las unidades secundarias; cada laboratorio tiene objetivo, consigna inicial y artefacto esperado no vacios, junto con una lista que contiene al menos un paso de verificacion no vacio.
- **AC-FR-008**: Una revision del conjunto de contenido confirma que todos los nombres, comercios, cuentas, montos y situaciones estan marcados o son reconocibles como ficticios y que no aparece informacion personal real.
- **AC-FR-009-011**: Tras publicar una unidad, una matriz de intentos de cambio y eliminacion sobre la version, sus opciones y su laboratorio produce cero mutaciones; publicar una correccion valida crea el siguiente numero vigente y deja la instantanea anterior identica.
- **AC-FR-012-014**: La primera carga reconoce tracks por titulo, modulos por track y titulo, unidades controladas por modulo y posicion, opciones por version y posicion y laboratorios por version. Tanto una instalacion con el titulo canonico "Fundamentos de negocio para equipos técnicos" como una con su alias legacy sin tilde convergen en una unica identidad con el titulo canonico. Si las dos unidades demo iniciales reconocidas difieren, publica como maximo una nueva version por cada una y conserva sus versiones anteriores; una segunda carga sin cambios conserva todas las identidades y cantidades y crea o modifica cero registros y cero versiones. Si una posicion esperada contiene una unidad no reconocible como controlada, no la adopta ni la modifica y se aplica el rechazo atomico de FR-015.
- **AC-FR-015**: Una falla provocada en cada etapa significativa de la carga conserva exactamente el estado completo anterior y un reintento posterior puede alcanzar el resultado esperado sin duplicados. Agregar una unidad ajena o colocarla en una posicion esperada de cualquiera de los modulos de destino antes de cargar produce un rechazo con conflicto o colision identificable, cero cambios y ninguna conversion, reubicacion, nueva version, retirada ni sobrescritura de esa unidad.
- **AC-FR-016**: Un aprendiz recorre ambos tracks y recibe exactamente las diez versiones vigentes en orden, con sus microlecciones, casos, opciones y retroalimentacion, sin recibir una version historica por error.
- **AC-FR-017**: La revision de conformidad identifica evidencia automatizada para publicacion y versionado, inmutabilidad, atomicidad, idempotencia y autorizacion de la cuenta autora; confirma que el comando no acepta identidad por argumentos, que `catalog` consume el servicio publico de consulta de `accounts` sin importar ni consultar directamente su modelo y que una configuracion ausente, invalida o no autorizada falla sin escrituras y sin exponer identificadores internos.
- **AC-FR-018**: Dos ejecuciones liberadas simultaneamente contra el mismo estado compatible terminan sin error; ambas reportan el mismo resultado logico y una inspeccion final encuentra exactamente los dos tracks, sus dos modulos, diez unidades vigentes y un solo conjunto esperado de versiones, opciones y laboratorios.

### Key Entities *(include if feature involves data)*

- **Track**: Ruta publicada que agrupa y ordena las unidades; en este alcance existen el track principal de siete unidades y el secundario de tres.
- **Unidad de aprendizaje**: Elemento editorial ordenado dentro de un track que conserva su identidad logica y referencia una unica version publicada vigente.
- **Version publicada**: Instantanea numerada, trazable e inmutable de una unidad con microleccion, caso, duracion, metadatos editoriales y un estado editorial persistido cuyo valor en este alcance es `published`.
- **Opcion**: Alternativa ordenada de una version publicada con valoracion pedagogica, consecuencia y explicacion.
- **Laboratorio**: Actividad practica vinculada a una version del track principal, compuesta por objetivo, consigna, artefacto esperado y lista de verificacion.
- **Definicion de carga**: Archivo JSON versionado y no ejecutable que contiene el conjunto controlado y aprobado de temas, textos, metadatos, conteo de tres o cuatro opciones por unidad y ubicaciones estables dentro de los dos tracks y sus modulos, y que permite crear, completar o reconocer el contenido sin duplicarlo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Despues de una carga correcta, el 100% de las consultas de comprobacion encuentra exactamente siete unidades vigentes en el track principal y tres en el secundario, en el orden tematico definido.
- **SC-002**: El 100% de las diez unidades vigentes contiene titulo, objetivo de aprendizaje, microleccion, caso, tres o cuatro opciones completas, al menos una opcion optima, fuente, autor, fecha de revision, fecha de publicacion y estado editorial `published`; las siete principales tienen un laboratorio completo y las tres secundarias no.
- **SC-003**: El 100% de los casos invalidos de la matriz de limites y metadatos se rechaza sin versiones parciales, y el 100% de los casos validos se publica una sola vez.
- **SC-004**: El 100% de los intentos de modificar o eliminar una version publicada o sus componentes deja el contenido original sin cambios.
- **SC-005**: Dos ejecuciones consecutivas de la carga producen cero duplicados, cero versiones adicionales en la segunda ejecucion y ninguna diferencia en identidades, valores, relaciones, orden o cantidades.
- **SC-006**: El 100% de las fallas provocadas durante la carga conserva el estado completo previo, sin tracks ni unidades parcialmente actualizados.
- **SC-007**: En una revision con cinco aprendices de las audiencias objetivo, cada participante completa las diez unidades en sesiones separadas; para cada unidad, al menos cuatro de los cinco participantes terminan en cinco minutos o menos y explican la decision optima usando la consecuencia y la explicacion mostradas.
- **SC-008**: Una revision editorial del conjunto de diez unidades encuentra cero datos personales reales y confirma fuente, autor y fecha de revision en todas las versiones vigentes.
- **SC-009**: El 100% de una matriz de ejecuciones simultaneas de la carga termina correctamente y conserva un unico estado logico completo, sin registros duplicados ni cambios parciales.

## Assumptions

- El comando de despliegue crea los dos tracks y un modulo por track cuando faltan, o reconoce los existentes por sus titulos estables; completa las unidades dentro de esos mismos modulos y conserva sus identidades logicas.
- Las dos unidades demo iniciales forman parte de las diez unidades objetivo. Si su contenido vigente no coincide con la definicion aprobada, se conserva la version historica y se publica una version posterior valida en lugar de modificarla.
- "Solo el track principal lleva laboratorio" significa que cada una de sus siete unidades tiene exactamente un laboratorio y que ninguna de las tres unidades secundarias lo tiene.
- Cinco minutos es el tiempo maximo objetivo por unidad y se valida con el protocolo de SC-007; no impone un limite de sesion ni interrumpe al aprendiz.
- Una fuente es una referencia editorial no vacia que permite reconocer la procedencia del contenido; el autor es la identidad editorial responsable y la fecha de revision no puede ser futura.
- La cuenta autora de despliegue existe antes de ejecutar la carga, permanece activa y tiene el rol `content_admin`. Su referencia se entrega al proceso mediante configuracion privada del servidor, nunca mediante argumentos del comando, y no se imprime ni se registra.
- La definicion controlada de contenido es un archivo JSON versionado bajo `catalog/content_data/` y proporciona valores deterministas para metadatos, textos, opciones y laboratorios. Puede actualizarse como dato sin modificar codigo Python; la ubicacion por track, modulo y posicion identifica cada unidad aunque cambie el texto entre versiones.
- La constitucion vigente es la autoridad para las reglas globales de dominio, autorizacion, privacidad, idempotencia, versionado y verificacion; esta especificacion solo concreta el conjunto de contenido y sus resultados esperados.

## Scope Boundaries

### In Scope

- Publicar y versionar las siete unidades del track principal y las tres del secundario.
- Validar componentes pedagogicos, cantidad y calidad minima de opciones y metadatos editoriales.
- Incluir laboratorios solo en las unidades del track principal.
- Conservar la inmutabilidad de cada version publicada y sus componentes.
- Cargar y reconciliar el conjunto de contenido de forma atomica e idempotente.
- Dejar las diez unidades vigentes disponibles para aprendices en el orden definido.

### Out of Scope

- Interfaz de autoria o edicion desde el navegador.
- Reordenamiento o retiro de unidades.
- Flujos de aprobacion editorial.
- Generacion de contenido con inteligencia artificial.
- Cambios en inscripcion, progreso, puntuacion, rachas, ligas o metricas.
- Ejecucion de agentes dentro de la plataforma; los agentes aparecen unicamente como tema pedagogico del track principal.

## Dependencies

- Los contratos existentes de tracks, modulos, unidades, versiones, opciones y laboratorios deben estar disponibles y conservar sus identidades y relaciones definidas.
- El modulo `accounts` debe publicar un servicio de consulta que resuelva y bloquee la cuenta autora, compruebe que esta activa y posee el rol `content_admin`, y devuelva un resultado generico cuando la referencia sea invalida o no autorizada; esta feature puede modificar `accounts/services/queries.py` y sus pruebas bajo `tests/accounts/` para establecer esa frontera.
- El entorno de despliegue debe provisionar la cuenta autora y su referencia privada antes de ejecutar la carga; si la configuracion falta o no resuelve una cuenta autorizada, el comando debe fallar de forma generica y no escribir contenido.
- El comando de despliegue de esta feature es la unica entrada para crear o reconciliar este conjunto de contenido; los tracks, modulos y unidades preexistentes deben poder reconocerse por las claves logicas descritas en FR-012.
- El catalogo de aprendizaje debe consumir la version vigente de cada unidad publicada y respetar su orden.
