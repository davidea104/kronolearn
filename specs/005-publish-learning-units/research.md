# Phase 0 Research: Publicacion de unidades de aprendizaje

## Servicio de creacion de borradores

**Decision**: Implementar la firma estable `create_content_draft(module, actor, payload)` como una operacion atomica que vuelve a cargar y bloquea primero al actor y luego al modulo. El `payload` admite un unico campo, `expected_revision`, entero positivo. El servicio valida la revision, bloquea las unidades del modulo, exige que sus posiciones formen una secuencia consecutiva y crea el borrador en la siguiente posicion; despues incrementa la revision del modulo y devuelve el `ContentItem` creado.

**Rationale**: El modelo no contiene texto mutable de borrador: el unico dato propio de una unidad antes de publicar es su posicion. Asignarla en el servicio evita que el comando decida orden, y la revision esperada convierte reintentos o escrituras concurrentes en conflictos detectables.

**Alternatives considered**:

- Aceptar `position` en el payload: descartado porque permitiria huecos y trasladaria al llamador una regla de orden que pertenece al dominio.
- Usar `max(position) + 1` sin bloquear el modulo: descartado porque dos escritores podrian elegir la misma posicion.
- Crear unidades directamente desde el comando: descartado porque duplicaria reglas de dominio fuera del servicio.

## Servicio de publicacion de contenido

**Decision**: Implementar `publish_content_item(content_item, actor, payload)` como una operacion atomica que bloquea al actor y a la unidad, valida `expected_revision` y crea una instantanea completa. El payload tiene esta forma cerrada:

```text
expected_revision: entero positivo
title: texto no vacio, maximo 160
learning_objective: texto no vacio, maximo 1000
lesson_text: texto no vacio
case_prompt: texto no vacio
source: texto no vacio, maximo 500
reviewed_on: fecha no futura
choices: secuencia de 3 o 4 elementos
  position: entero consecutivo desde 1
  text: texto no vacio, maximo 1000
  rating: OPTIMAL | PARTIAL | INCORRECT
  consequence: texto no vacio
  explanation: texto no vacio
lab: nulo o estructura
  objective: texto no vacio, maximo 1000
  initial_prompt: texto no vacio
  expected_artifact: texto no vacio
  verification_checklist: secuencia no vacia de textos no vacios
```

El autor se deriva del actor persistido y autorizado; el numero de version se calcula como `published_version + 1`, el servicio fija el estado editorial `PUBLISHED` y `published_at` lo asigna la base mediante el modelo. El JSON y los llamadores no pueden elegir ese estado. El servicio crea version, opciones y laboratorio antes de marcar la unidad como publicada, incrementa la revision de la unidad y revierte todo ante cualquier error.

**Rationale**: Una instantanea autocontenida permite validar la publicacion completa antes de escribir y preserva las versiones anteriores. Derivar autor, version y fecha impide que el comando falsifique metadatos autoritativos.

**Alternatives considered**:

- Crear primero opciones o laboratorios como borradores: descartado porque esos modelos son inmutables y solo pertenecen a una version publicada.
- Aceptar `author`, `version_number` o `published_at` en el payload: descartado porque son valores derivados por el servidor.
- Actualizar la version vigente cuando cambia el contenido: descartado porque rompe la trazabilidad historica.

## Validacion y errores de dominio

**Decision**: Usar `PermissionDenied` para actor inexistente, inactivo o sin rol de administrador de contenido; `ValidationError` con errores por campo para payloads invalidos; y excepciones locales explicitas `ContentRevisionConflict` y `ContentLoadConflict` para revisiones obsoletas y colisiones de la carga. Los mensajes del comando son genericos, no incluyen correo ni UUID, y convierten esas excepciones en `CommandError` sin capturar errores inesperados.

La publicacion valida, antes de escribir, todos los textos, limites de campos, fecha, cantidad y secuencia de opciones, valores de `rating`, ausencia de textos de opcion repetidos, presencia de al menos una opcion optima y estructura completa del laboratorio opcional.

**Rationale**: Las dos firmas estables devuelven entidades, por lo que los rechazos deben expresarse como excepciones. Separar conflicto de validacion permite al cargador informar una colision operativa sin confundirla con contenido editorial invalido.

**Alternatives considered**:

- Cambiar las firmas para devolver `CatalogCommandOutcome`: descartado porque feature 004 fijo los tipos de retorno publicos.
- Propagar `IntegrityError`: descartado porque expone detalles de persistencia y no distingue una revision obsoleta de un payload invalido.
- Ampliar `CatalogChangeLog` para unidades: descartado porque requeriria modificar modelos cerrados y una migracion innecesaria.

## Orquestacion del conjunto de contenido

**Decision**: Añadir en `catalog.services.content` un servicio de aplicacion `load_learning_content(actor_ref, definitions)` que controla toda la reconciliacion dentro de una unica `transaction.atomic`. El comando `load_learning_content` obtiene `actor_ref` exclusivamente de `settings.CONTENT_AUTHOR_ACCOUNT_ID`, carga y valida el corpus JSON, invoca ese servicio y presenta un resumen sanitizado; no acepta identidad por argumentos ni consulta o escribe modelos.

El servicio llama a `accounts.services.queries.resolve_content_admin` para resolver, bloquear y autorizar al actor sin leer `Account` directamente, bloquea `CatalogState` como mutex global y procesa tracks, modulos y unidades en el orden fijo de la definicion. Reutiliza los servicios existentes de tracks y modulos y los dos servicios implementados por esta feature. Devuelve un resultado inmutable con `changed`, cantidades finales y cantidades de entidades o versiones creadas.

**Rationale**: La reconciliacion, la deteccion de colisiones y la atomicidad son reglas de dominio, no responsabilidades de un adaptador CLI. El bloqueo global ya existe, ordena las mutaciones del catalogo y hace que una segunda ejecucion concurrente observe el estado final de la primera.

**Alternatives considered**:

- Coordinar transacciones y consultas desde `Command.handle`: descartado porque convertiria el comando en una segunda autoridad de negocio.
- Mantener solo transacciones por unidad: descartado porque una falla podria dejar uno de los tracks parcialmente cargado.
- Crear un lock o tabla nueva: descartado porque `CatalogState` ya ofrece un punto de serializacion respaldado por PostgreSQL.

## Identidad natural y reconciliacion

**Decision**: No agregar claves persistentes de linaje. Reconocer tracks por `title_key`, modulos por `(track, title_key)`, unidades por `(module, position)`, opciones por `(content_version, position)` y laboratorio por su relacion uno a uno. El titulo canonico secundario es `Fundamentos de negocio para equipos técnicos`; la variante sin tilde se acepta solo como alias legacy y converge al titulo canonico. Cada fuente de unidad controlada empieza con un marcador estable y unico, por ejemplo `KronoLearn curriculum 005/principal/01`, seguido de la referencia editorial legible.

Una unidad existente en una posicion esperada es compatible solo si cumple una de estas condiciones:

1. Es un borrador sin versiones, por lo que no existe contenido publicado que adoptar o sobrescribir.
2. Su version vigente tiene el marcador estable de esa unidad.
3. Es una de las dos unidades iniciales de feature 004 en posicion 1 y coincide con la huella legacy completa: ubicacion, fuente `KronoLearn demo`, textos, opciones y laboratorio conocidos.

Antes de modificar nada, la carga comprueba que las posiciones existentes sean un prefijo consecutivo de la definicion, que no haya unidades adicionales y que cada posicion ocupada sea compatible. Para una unidad compatible compara la instantanea vigente completa, incluidas opciones y laboratorio, ignorando solo IDs, marcas temporales y el autor de una instantanea ya valida. Si coincide, no escribe; si difiere, publica exactamente una version posterior. Una unidad incompatible o adicional produce `ContentLoadConflict` y revierte toda la carga.

**Rationale**: Las restricciones unicas existentes proporcionan las identidades necesarias. El marcador de fuente evita identificar contenido ajeno solo por titulo o texto, mientras la huella legacy permite incorporar sin duplicar las dos unidades creadas por feature 004.

**Alternatives considered**:

- Agregar `slug`, `seed_key` o `definition_hash` a los modelos: descartado porque no es indispensable y abriria modelos y migraciones fuera del alcance.
- Adoptar cualquier unidad por posicion: descartado porque podria convertir contenido ajeno.
- Comparar solo el titulo vigente: descartado porque no demuestra linaje ni igualdad de la instantanea.

## Datos de contenido

**Decision**: Crear `catalog/content_data/learning_units.json` como fuente autoritativa no ejecutable para dos tracks, un modulo por track y diez unidades. Cada definicion contiene todos los textos, metadatos, opciones, laboratorio opcional, marcador de fuente y huella legacy cuando corresponda. La fecha de revision es un valor fijo del contenido, no la fecha de ejecucion. `catalog/content_data/definitions.py` define dataclasses congeladas y un parser que rechaza claves desconocidas o faltantes; `catalog/content_data/__init__.py` publica la funcion de carga.

El parser no importa modelos Django ni ejecuta consultas. Antes de iniciar mutaciones valida tipos, campos cerrados, cardinalidades 7/3, posiciones consecutivas, tres o cuatro opciones segun cada unidad, siete laboratorios principales, cero secundarios, marcadores unicos y titulo canonico. La revision editorial del PR aprueba el contenido del JSON; las pruebas validan su estructura y reglas sin mantener una segunda copia completa del corpus.

**Rationale**: Separar datos no ejecutables y mecanismo permite revisar, versionar y reemplazar el corpus sin modificar codigo fuente. Las estructuras inmutables resultantes impiden que una ejecucion altere la definicion compartida.

**Alternatives considered**:

- Diccionarios mutables dentro del comando: descartado por acoplar contenido, transporte y reglas.
- Modulo Python con el corpus: descartado porque obligaria a modificar codigo fuente para actualizar contenido y violaria el principio 3.
- YAML: descartado para evitar una dependencia de parseo adicional; JSON dispone de parser en la biblioteca estandar.
- Generar textos u opciones durante la ejecucion: descartado porque impediria resultados deterministas.

## Comando y cuenta autora

**Decision**: Crear `catalog/management/commands/load_learning_content.py` sin argumentos de identidad. `kronolearn/settings/base.py` obtiene opcionalmente `CONTENT_AUTHOR_ACCOUNT_ID` del entorno para no bloquear otros procesos Django; el comando exige que tenga valor antes de invocar el dominio. El entorno debe provisionar previamente la cuenta activa con `content_admin`. El comando no crea cuentas ni roles, no acepta contenido o identidad por argumentos y no incorpora `--dry-run` ni confirmaciones de demo. `accounts.services.queries.resolve_content_admin` resuelve la referencia bajo bloqueo y verifica estado y rol en el momento de la operacion. La referencia no se imprime ni se registra.

El comando termina con codigo 0 tanto cuando crea o actualiza contenido como cuando ya estaba convergido. Los conflictos, la falta de autorizacion y los datos invalidos terminan con codigo distinto de cero y un mensaje sin identificadores internos.

**Rationale**: Una carga de despliegue debe atribuir versiones a una cuenta persistida y autorizada sin aceptar una identidad manipulable en la invocacion. La configuracion privada vincula el proceso no interactivo con una identidad server-side y el servicio propietario mantiene la lectura y autorizacion de cuenta.

**Alternatives considered**:

- Reutilizar o modificar `seed_demo`: descartado porque es una operacion de demostracion cerrada y con datos de cuenta propios.
- Aceptar `--actor-id`: descartado porque una identidad de cuenta no puede viajar como argumento de un proceso no interactivo.
- Buscar al autor por correo desde el comando: descartado para evitar que el adaptador consulte `accounts` y para minimizar el manejo de datos personales.
- Crear automaticamente una cuenta de sistema: descartado porque introduciria credenciales y gestion de roles fuera del alcance.

## Estrategia de concurrencia

**Decision**: Mantener un orden unico de bloqueo: actor, `CatalogState`, tracks por clave estable, modulos por clave estable y unidades por posicion. El lock de `CatalogState` serializa las cargas completas; los locks locales de modulo y unidad mantienen correctos los dos servicios cuando se invocan fuera del cargador. Las restricciones unicas existentes siguen siendo la ultima defensa ante carreras.

La prueba concurrente usa `TransactionTestCase`, dos conexiones PostgreSQL y una barrera para iniciar dos cargas sobre el mismo estado. Ambas deben devolver exito; una puede informar cambios y la otra debe observar convergencia sin escribir.

**Rationale**: Un orden fijo evita interbloqueos previsibles y el lock global permite cumplir simultaneamente atomicidad total e idempotencia concurrente sin esquema adicional.

**Alternatives considered**:

- Confiar solo en `get_or_create`: descartado porque no protege una reconciliacion compuesta ni evita versiones extra.
- Reintentar despues de cada `IntegrityError`: descartado porque complica la transaccion y puede ocultar estados parciales.
- Probar concurrencia con SQLite: descartado porque no reproduce los locks de fila de produccion.

## Pruebas y migraciones

**Decision**: Mantener las pruebas de cuenta bajo `tests/accounts/test_queries.py` y las de contenido bajo `tests/catalog/`. Usar `TestCase` para parser JSON, payloads, autorizacion, versionado, inmutabilidad, huellas, comando, datos 7/3 e idempotencia secuencial. Usar `TransactionTestCase` marcado para PostgreSQL para la migracion, carreras de creacion y publicacion y dos cargas simultaneas. Ejecutar primero los tests afectados y despues la suite completa y Ruff.

Crear `catalog/migrations/0003_contentversion_editorial_status.py`: agrega `ContentVersion.editorial_status` con el unico valor permitido `PUBLISHED`, rellena las versiones existentes con ese valor y añade un check constraint. El modelo usa un `TextChoices` propio porque el estado editorial de una unidad coincide con su publicacion, mientras tracks y modulos conservan su vocabulario `APPROVED` existente.

**Rationale**: SQLite es suficiente para contratos deterministas, mientras PostgreSQL es la evidencia autoritativa para migraciones y concurrencia. Persistir el estado editorial satisface la trazabilidad constitucional y evita depender de una interpretacion implicita.

**Alternatives considered**:

- Representar la aprobacion solo por la existencia de `ContentVersion`: descartado porque no conserva explicitamente el estado editorial requerido.
- Probar todo solo con SQLite: descartado porque sus primitivas de bloqueo difieren de PostgreSQL.
- Editar CI: descartado porque el job PostgreSQL existente ya ejecuta `tests.catalog` y el archivo esta fuera del alcance permitido.

## Integracion de despliegue y validacion editorial

**Decision**: Actualizar `.env.example` y `docs/deployment/railway.md`. Railway debe definir `CONTENT_AUTHOR_ACCOUNT_ID` como variable privada y ejecutar en Pre-Deploy `python manage.py migrate --noinput` seguido de `python manage.py load_learning_content`; el proceso web se inicia solo despues de ambos. No se agrega `Procfile` porque la configuracion actual vive en Railway y el repositorio no contiene uno.

SC-007 se valida fuera de CI mediante una revision moderada con cinco aprendices de las audiencias objetivo. Para cada unidad se mide desde que se muestra su titulo y contenido hasta que el participante registra una opcion y explica la decision; se usa una sesion independiente por unidad, se registran tiempos anonimizados y se exige que al menos cuatro de cinco participantes terminen en cinco minutos o menos. El reporte editorial es evidencia de aceptacion y no contiene identificadores de cuenta.

**Rationale**: Documentar la configuracion operativa en la guia existente evita introducir infraestructura paralela. Separar evidencia humana de pruebas automatizadas hace medible el objetivo pedagogico sin fingir que una suite puede probar tiempo de lectura y comprension.

**Alternatives considered**:

- Ejecutar la carga al arrancar cada proceso web: descartado porque mezcla despliegue y serving y multiplica la concurrencia innecesariamente.
- Crear un `Procfile`: descartado porque Railway ya administra build, pre-deploy y start, y no existe ese patron en el repositorio.
- Convertir SC-007 en una prueba automatizada: descartado porque mide comportamiento humano, no tiempo de ejecucion del software.