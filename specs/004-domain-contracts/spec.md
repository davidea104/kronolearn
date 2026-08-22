# Feature Specification: Contratos y esqueleto de dominio

**Feature Branch**: `004-domain-contracts`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "Fijar todos los contratos compartidos del dominio para permitir el desarrollo paralelo de autoría de contenido, inscripción, sesión diaria, intento y retroalimentación, ruta y progreso, y puntos y racha, sin entregar interfaz funcional."

## Clarifications

### Session 2026-08-21

- Q: ¿Cómo debe representar el sistema cuál es la versión vigente de un contenido? → A: `ContentItem` guarda el número vigente y la bandera de `ContentVersion` se deriva como valor de solo lectura.
- Q: ¿Qué debe ocurrir si un receptor de `attempt_registered` falla mientras se registra un intento? → A: Se revierte toda la operación; no persiste el intento ni ningún efecto derivado.
- Q: ¿Cómo debe representar `ScoreEvent` los puntos base y el bono de racha originados por un mismo intento? → A: Un único evento por intento con puntos base más bono y causa `attempt`.
- Q: ¿Cómo deben devolver resultados `content_metrics` y `engagement_metrics` sin cambiar sus firmas cuando se definan nuevas métricas? → A: Una estructura estable con contexto, cantidad de personas, supresión y mapa de métricas.
- Q: ¿Cuántas cuentas debe crear `seed_demo` para cada rol? → A: Una learner y una content_admin; dos cuentas en total.
- Q: ¿Cómo debe identificar `seed_demo` a sus cuentas cuando `Account.email` es obligatorio, sin incumplir la prohibición de exponer correos? → A: Correos deterministas, no personales y reservados bajo `.invalid`, almacenados solo en `Account` y nunca expuestos.
- Q: ¿Qué nivel de garantía debe entregar esta feature para la consecutividad de `ContentItem` y las fechas canónicas de `WeeklySeason`? → A: Constraints por fila ahora; `current_season` garantiza semanas canónicas y los futuros servicios propietarios garantizan invariantes agregados.
- Q: ¿Qué debe verificar esta feature sobre `attempt_registered` mientras `register_attempt` continúe siendo un STUB? → A: La infraestructura síncrona y transaccional mediante un harness; creación, replay y reintento reales se verifican al implementar el productor.
- Q: ¿Cómo debe derivarse de forma estable el digest de las claves de idempotencia para intentos y eventos de puntuación? → A: Con `security_digest`, la entrada canónica completa y los propósitos fijos `learning.attempt.idempotency` y `gamification.score-event.idempotency`.
- Q: ¿Quién debe mantener los contadores persistidos de `SeasonParticipation` sin romper la frontera entre `learning` y `gamification`? → A: `gamification` es el único escritor y reacciona a `attempt_registered` y al contrato reservado `session_completed`.
- Q: ¿Debe cada app registrar únicamente los eventos que realmente consume, o receptores para ambos eventos aunque uno no le corresponda? → A: Cada app registra una sola vez únicamente los eventos que consume: `learning` consume `attempt_registered`; `gamification` consume `attempt_registered` y `session_completed`.
- Q: ¿Cómo debe demostrarse el cumplimiento de SC-006 y SC-009 sobre localizar contratos y rutas sin aclaraciones verbales? → A: Mediante pruebas automatizadas de trazabilidad y ownership, sin requerir revisiones humanas cronometradas.
- Q: ¿Qué debe garantizar ahora la base de datos para un `ScoreEvent` con causa `session_completed`? → A: La base acepta el recibo con sus constraints genéricos; el receptor futuro garantiza monto cero y ausencia de intento.
- Q: ¿Cómo debe verificarse que la navegación conserve semántica, operación por teclado y foco visible al modificar la plantilla base? → A: Con pruebas automatizadas rápidas sobre el HTML renderizado y las reglas o clases de foco existentes, sin navegador ni comprobación manual.
- Q: ¿Qué evidencia debe exigir esta feature sobre las entradas y propósitos exactos de los digests mientras los productores continúan siendo STUB? → A: Validación automatizada de contratos y docstrings, más pruebas directas de determinismo y separación de propósito del helper; la integración runtime corresponde a las features productoras.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Desarrollar features en paralelo sobre contratos estables (Priority: P1)

Como integrante de uno de los seis equipos de la línea base, quiero disponer de entidades, firmas, eventos y puntos de integración definitivos para implementar mi feature sin editar archivos compartidos ni esperar a otros equipos.

**Why this priority**: La finalidad de esta feature es eliminar bloqueos y conflictos entre las seis ramas paralelas. Sin contratos estables, ninguna de las demás historias cumple el objetivo de coordinación.

**Independent Test**: Se asigna una copia limpia del repositorio a cada uno de los seis equipos. Cada equipo localiza sus contratos y rutas de propiedad, importa o invoca sus firmas asignadas y prepara su trabajo sin modificar modelos, migraciones, composición raíz, plantilla base ni agregadores compartidos.

**Acceptance Scenarios**:

1. **Given** la línea base instalada, **When** cada equipo consulta el documento de contratos, **Then** identifica sin decisiones pendientes las entidades, operaciones, eventos y archivos que puede consumir o modificar.
2. **Given** las seis ramas de feature creadas desde la misma línea base, **When** cada equipo añade trabajo solo en sus rutas asignadas, **Then** ninguna rama necesita editar un modelo, una migración o un punto de composición bloqueado.
3. **Given** un contrato marcado como STUB, **When** un consumidor lo importa e inspecciona, **Then** encuentra la firma y semántica definitivas y su ejecución falla de forma explícita sin producir efectos parciales.
4. **Given** un contrato marcado como IMPLEMENTAR, **When** un consumidor lo usa con datos válidos, **Then** obtiene el resultado definido sin depender de ninguna feature posterior.

---

### User Story 2 - Validar una línea base íntegra y desacoplada (Priority: P1)

Como mantenedor, quiero aplicar una sola evolución coordinada del dominio y verificar sus invariantes para que las features posteriores no creen esquemas divergentes ni acoplamientos entre módulos.

**Why this priority**: Los contratos solo permiten trabajo paralelo si la estructura compartida es coherente, íntegra y estable desde el inicio.

**Independent Test**: Desde una base vacía se aplica toda la evolución de datos, se crean ejemplos válidos e inválidos de cada entidad y se comprueban las restricciones, la inmutabilidad, los límites temporales y el desacoplamiento por eventos.

**Acceptance Scenarios**:

1. **Given** una base de datos vacía compatible, **When** se aplica la evolución completa, **Then** todas las entidades compartidas quedan disponibles sin intervención manual ni migraciones divergentes.
2. **Given** dos operaciones con la misma clave de idempotencia, **When** ambas intentan persistirse, **Then** la segunda no puede crear un segundo intento, evento de puntuación ni registro equivalente.
3. **Given** una versión de contenido publicada, **When** cualquier operación intenta modificarla o eliminarla, **Then** el contenido histórico permanece exactamente igual.
4. **Given** un intento recién registrado por una feature futura, **When** se publica el evento acordado dentro de su operación atómica, **Then** los consumidores pueden reaccionar sin que el productor importe sus servicios.

---

### User Story 3 - Preparar y repetir un entorno de demostración (Priority: P2)

Como persona desarrolladora o revisora, quiero cargar un conjunto mínimo y reproducible de datos para trabajar en cualquier feature sin depender de que otra rama haya implementado sus flujos.

**Why this priority**: Los datos compartidos reducen el tiempo de preparación y permiten validar contratos desde el primer día, aunque todavía no exista una interfaz funcional.

**Independent Test**: En un entorno permitido se carga dos veces el conjunto de demostración y se verifica que contiene exactamente los mismos tracks, módulos, contenidos, cuentas y temporada tras ambas ejecuciones.

**Acceptance Scenarios**:

1. **Given** un entorno de desarrollo vacío, **When** se solicita la carga de demostración, **Then** quedan disponibles los dos tracks definidos, sus módulos y contenidos válidos, una cuenta learner, una cuenta content_admin y la temporada vigente.
2. **Given** los datos de demostración ya cargados, **When** se repite la carga, **Then** no aparecen duplicados ni cambian las identidades lógicas de los registros existentes.
3. **Given** un entorno no destinado a desarrollo, **When** se intenta cargar datos sin confirmación explícita, **Then** la operación se rechaza sin crear cuentas ni contenido.
4. **Given** un entorno no destinado a desarrollo con confirmación explícita, **When** se cargan cuentas demo, **Then** ninguna queda protegida por una contraseña conocida o publicada.

---

### User Story 4 - Planificar backlog sin alterar la línea base (Priority: P3)

Como responsable de una feature futura de liga semanal, métricas, insignias, repaso o meta semanal, quiero consultar agregados y contratos ya definidos para especificar mi trabajo sin cambiar la estructura compartida de la línea base.

**Why this priority**: Estas features no forman parte de la entrega inmediata, pero reservar sus dependencias evita una segunda ronda de cambios transversales.

**Independent Test**: Para cada una de las cinco features de backlog se traza de dónde obtiene contenido, intentos, progreso, puntuación, racha, temporada y participación sin añadir campos a las entidades de línea base ni modificar sus firmas públicas.

**Acceptance Scenarios**:

1. **Given** la necesidad de ordenar una liga semanal, **When** se revisan los contratos, **Then** existen temporada, participación y una operación de clasificación reservada.
2. **Given** la necesidad de métricas administrativas, **When** se revisan los contratos, **Then** existen operaciones agregadas reservadas para contenido y participación.
3. **Given** la necesidad de calcular insignias, repaso o meta semanal a partir de actividad existente, **When** se revisan las entidades, **Then** los datos necesarios pueden obtenerse de intentos, progreso, eventos, rachas y participaciones sin cambiar esos contratos.

### Edge Cases

- Dos procesos intentan crear simultáneamente la misma temporada semanal: solo una temporada puede quedar persistida y ambos consumidores obtienen la misma identidad lógica.
- Un momento cae exactamente al inicio del lunes o al final del domingo en la zona horaria fija del proyecto: pertenece a una única temporada con límites correctos.
- Una opción elegida no pertenece a la versión de contenido presentada: el contrato de intento debe rechazar la combinación antes de generar efectos derivados.
- Una versión marcada como vigente compite con otra del mismo contenido: solo una puede conservar la condición de vigente.
- Una versión publicada tiene menos de tres opciones, más de cuatro o ninguna óptima: el conjunto no puede considerarse publicable ni válido para demostración.
- Dos inscripciones intentan relacionar la misma cuenta y el mismo track: solo una relación puede existir.
- Un progreso presenta valores negativos o más contenidos completados que contenidos totales: el estado se rechaza.
- Dos intentos o eventos de puntuación reutilizan una clave de idempotencia: la restricción persistente impide el duplicado aunque las solicitudes sean concurrentes.
- Una temporada creada mediante `current_season` siempre usa lunes y domingo consecutivos; cualquier temporada solapada se rechaza en persistencia, incluso si se intenta insertar fuera del servicio.
- Un receptor de eventos falla: la excepción revierte el intento y todos los efectos derivados; un reintento puede reutilizar la misma clave de idempotencia porque la operación fallida no dejó registros persistidos.
- Una referencia inválida llega a una ruta de auditoría: solo puede conservarse su resumen no reversible, nunca el valor recibido.
- Una entrada de navegación apunta a una ruta todavía no implementada: el registro no rompe la navegación ni obliga a editar la plantilla compartida.
- Una feature posterior concluye que necesita una entidad o migración no prevista: debe detenerse y solicitar una ampliación explícita del contrato antes de modificar el esquema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La feature DEBE entregar exclusivamente contratos, estructura compartida, datos de demostración y verificaciones; NO DEBE entregar flujos funcionales visibles para aprendices ni administradores.
- **FR-002**: La feature DEBE extender el dominio existente sin cambiar el comportamiento público vigente de identidad, roles, administración de tracks y módulos, ordenamiento, publicación, desactivación ni auditoría.
- **FR-003**: Todos los modelos y evoluciones de datos compartidos enumerados en esta especificación DEBEN crearse en esta feature. Una feature posterior que requiera otra evolución DEBE solicitarla explícitamente antes de modificar el esquema.
- **FR-004**: Toda firma pública marcada como STUB DEBE existir con parámetros, tipo de retorno y semántica documentados de forma definitiva, DEBE lanzar `NotImplementedError` al ejecutarse y NO DEBE producir efectos. Toda firma marcada como IMPLEMENTAR DEBE funcionar y estar verificada en esta feature.
- **FR-005**: El documento de contratos y los artefactos ejecutables DEBEN coincidir en nombres, parámetros, resultados, estados STUB o IMPLEMENTAR y reglas de ordenamiento.

### Data Contracts

- **FR-006**: `ContentItem` DEBE pertenecer a un único `Module`, ocupar una posición positiva y única dentro de ese módulo, conservar un estado editorial cerrado de borrador o publicado, identificar su número de versión publicada vigente y exponer una revisión que permita rechazar actualizaciones obsoletas con el mismo criterio ya usado por `Module`. La consecutividad desde 1 es una precondición del futuro servicio propietario de creación o reordenamiento y no se implementa en esta feature.
- **FR-007**: `ContentVersion` DEBE ser una instantánea inmutable de un `ContentItem`, con número incremental único dentro del contenido, título, objetivo de aprendizaje, texto de microlección, enunciado del caso, fuente, autor, fecha de revisión y fecha de publicación. DEBE exponer una bandera de vigencia de solo lectura, derivada al comparar su número con la versión publicada indicada por `ContentItem`; publicar una versión nueva NO DEBE modificar la instantánea anterior. Solo una versión por contenido puede resultar vigente y ninguna versión publicada puede mutarse o eliminarse.
- **FR-008**: `Choice` DEBE pertenecer a una única `ContentVersion` y conservar texto, posición, valoración pedagógica cerrada en óptima, parcialmente adecuada o incorrecta, consecuencia y explicación. Cada versión publicable DEBE tener entre tres y cuatro opciones con posiciones únicas y consecutivas y al menos una opción óptima. Las opciones de una versión publicada son inmutables.
- **FR-009**: `LabExercise` DEBE representar el laboratorio opcional y único de una `ContentVersion`, con objetivo, prompt inicial, artefacto esperado y checklist de verificación.
- **FR-010**: `Enrollment` DEBE relacionar de forma única una cuenta y un track, registrar la fecha de inscripción y conservar un estado cerrado de activa o retirada. La finalización del track se calcula mediante el contrato de sesión y no añade otro estado persistente.
- **FR-011**: `Attempt` DEBE referenciar la inscripción, la versión exacta presentada y la opción elegida; conservar la valoración resultante, fecha y hora, la condición de primer intento puntuable para esa inscripción y versión, y un digest de idempotencia globalmente único. La futura operación `register_attempt` DEBE derivarlo como `security_digest(idempotency_key, purpose="learning.attempt.idempotency")`, usando la clave opaca completa sin persistirla. La opción debe pertenecer a la versión presentada y solo puede existir un primer intento puntuable por combinación.
- **FR-012**: `Progress` DEBE ser único por inscripción y módulo, conservar contenidos completados, contenidos totales y aciertos acumulados, impedir valores negativos e impedir que los completados superen el total.
- **FR-013**: `ScoreEvent` DEBE conservar causa, monto, referencia opcional al intento, fecha y hora y un digest de idempotencia globalmente único. Para la causa estable `attempt`, el futuro servicio DEBE derivarlo como `security_digest(str(attempt.id), purpose="gamification.score-event.idempotency")`; otras causas deberán fijar su entrada canónica y propósito antes de implementarse. Para un intento puntuable DEBE existir como máximo un evento con referencia obligatoria a ese intento y monto total igual a sus puntos base más el bono de racha aplicable. Los montos pueden ser cero, pero ningún evento puede duplicarse por reintento. La persistencia DEBE aceptar un evento sin intento y con monto cero para la causa `session_completed`, pero esta feature NO DEBE imponer esa combinación como constraint específico de causa: el receptor futuro será responsable de producirla. La causa admite identificadores estables adicionales para hechos futuros sin cambiar la estructura del evento.
- **FR-014**: `Streak` DEBE ser único por cuenta y conservar longitud actual no negativa, máximo histórico no menor que la longitud actual y fecha opcional de última actividad.
- **FR-015**: `WeeklySeason` DEBE conservar fechas de inicio y fin únicas y ordenadas, sin solapamiento con otra temporada. La operación implementada `current_season` DEBE ser la ruta pública de creación y producir exactamente el intervalo de lunes a domingo que contiene el momento en la zona horaria fija del proyecto.
- **FR-016**: `SeasonParticipation` DEBE ser única por temporada y cuenta, y conservar puntos semanales, intentos puntuables correctos, intentos puntuables totales y sesiones completadas como cantidades no negativas; los intentos correctos no pueden superar los intentos totales. `gamification` es el único módulo autorizado a escribir estos contadores: sus futuros receptores reaccionarán a `attempt_registered` para puntos e intentos y a `session_completed` para sesiones completadas. El receptor futuro de sesión DEBE crear un `ScoreEvent` sin intento y con monto cero como recibo idempotente antes de incrementar `completed_sessions`; esta regla pertenece al servicio receptor, no a un constraint específico de causa en esta feature.
- **FR-017**: La cuenta existente DEBE seguir usando su único nombre visible como identidad pública. Esta feature NO DEBE añadir otros datos de perfil y ninguna clasificación puede exponer el correo electrónico.

### Service Contracts

Los nombres siguientes son parte del contrato público. Los tipos compuestos `AttemptResult`, `TrackProgress`, `LeaderboardEntry`, `ContentMetrics` y `EngagementMetrics` son estructuras inmutables y sus campos documentados forman parte de la firma estable.

| Module and operation | Result contract | Delivery state |
| --- | --- | --- |
| `catalog.services.content.publish_content_item(content_item, actor, payload)` | `ContentVersion`; publica una nueva instantánea válida y vigente sin alterar versiones anteriores | STUB |
| `catalog.services.content.create_content_draft(module, actor, payload)` | `ContentItem`; crea un borrador al final de la secuencia del módulo | STUB |
| `catalog.services.content.get_published_version(content_item)` | `ContentVersion` vigente o `None` | IMPLEMENTAR |
| `catalog.services.content.list_published_versions(track)` | Lista de versiones vigentes de contenidos publicados, ordenada por posición de módulo y contenido | IMPLEMENTAR |
| `learning.services.enrollment.enroll(account, track)` | `Enrollment`; devuelve una única inscripción activa sin duplicarla | STUB |
| `learning.services.enrollment.get_enrollment(account, track)` | `Enrollment` o `None` | IMPLEMENTAR |
| `learning.services.enrollment.list_enrollments(account)` | Consulta diferida de inscripciones de la cuenta en orden estable de fecha e identidad | IMPLEMENTAR |
| `learning.services.session.get_next_content_version(enrollment)` | Siguiente `ContentVersion` o `None` | STUB |
| `learning.services.session.is_track_completed(enrollment)` | Valor booleano derivado del contenido publicado y el progreso | STUB |
| `learning.services.attempts.register_attempt(enrollment, content_version, choice, idempotency_key)` | `AttemptResult` | STUB |
| `learning.services.attempts.list_attempts(enrollment)` | Consulta diferida de intentos en orden cronológico estable | IMPLEMENTAR |
| `learning.services.progress.recompute_progress(enrollment)` | `None`; reemplaza el agregado por el valor derivado de intentos válidos | STUB |
| `learning.services.progress.get_track_progress(enrollment)` | `TrackProgress` con porcentaje, módulos ordenados y precisión | STUB |
| `gamification.services.scoring.award_for_attempt(attempt)` | Único `ScoreEvent` de causa `attempt`, con puntos base más bono, o `None` si no es puntuable | STUB |
| `gamification.services.streaks.register_activity(account, activity_date)` | `Streak` | STUB |
| `gamification.services.streaks.streak_bonus(streak)` | Entero entre cero y el tope configurado | STUB |
| `gamification.services.seasons.current_season(moment)` | `WeeklySeason`; obtiene o crea de forma segura la temporada de lunes a domingo que contiene el momento | IMPLEMENTAR |
| `gamification.services.seasons.leaderboard(season)` | Lista ordenada de `LeaderboardEntry` sin datos privados de cuenta | STUB |
| `analytics.services.metrics.content_metrics(track=None)` | `ContentMetrics` agregado para todo el catálogo o un track | STUB |
| `analytics.services.metrics.engagement_metrics(window_days)` | `EngagementMetrics` agregado para una ventana positiva de días | STUB |

- **FR-018**: `AttemptResult` DEBE contener `attempt`, `rating`, `is_scoreable`, `consequence`, `explanation` y `source`. Su valoración y retroalimentación deben corresponder a la opción elegida y su fuente a la versión presentada.
- **FR-019**: `TrackProgress` DEBE contener porcentaje entre 0 y 100, colección ordenada de progresos por módulo y precisión entre 0 y 100; debe definir de forma estable el resultado para una inscripción sin intentos.
- **FR-020**: `LeaderboardEntry` DEBE contener únicamente nombre visible, posición y agregados semanales, sin correo ni identificador interno de cuenta. `ContentMetrics` y `EngagementMetrics` DEBEN ser tipos de resultado inmutables con `context`, `person_count`, `is_suppressed` y `values`. `context` identifica el alcance o la ventana solicitada sin incluir identificadores internos de cuenta; `person_count` es la cantidad no negativa de personas distintas del agregado; `is_suppressed` indica si el mínimo configurable impide revelar resultados; y `values` es un mapa de nombres estables a valores numéricos con unidades documentadas. Cuando `is_suppressed` es verdadero, `values` DEBE estar vacío. Añadir una métrica futura PUEDE añadir una clave documentada sin cambiar el tipo ni la firma del servicio.
- **FR-021**: `RATING_POINTS` DEBE estar implementado como el mapa inmutable óptima = 100, parcialmente adecuada = 50 e incorrecta = 0.
- **FR-022**: `STREAK_BONUS_STEP` DEBE valer 10 y `STREAK_BONUS_CAP` DEBE valer 50. El cálculo que consume estas constantes permanece como STUB.
- **FR-023**: Las consultas implementadas DEBEN limitarse a leer estado autoritativo, devolver resultados con orden determinista y no aplicar reglas reservadas para las features posteriores.

### Domain Event Contract

- **FR-024**: DEBEN existir los eventos públicos `learning.signals.attempt_registered`, con argumentos nombrados `attempt` y `result`, donde `result` cumple el contrato inmutable de `AttemptResult`, y `learning.signals.session_completed`, con argumentos nombrados `enrollment`, `completed_at` e `idempotency_key`. Esta feature reserva ambos sobres; sus productores funcionales permanecen como STUB.
- **FR-025**: El contrato DEBE exigir que la futura operación de registro emita el evento exactamente una vez para un intento nuevo, después de persistirlo y dentro de la misma operación atómica. Los receptores se ejecutan de forma síncrona y cualquier excepción DEBE propagarse para revertir el intento y todos sus efectos derivados. Un reintento idempotente que recupera el resultado previo NO DEBE volver a emitirlo; un reintento posterior a un rollback completo PUEDE reutilizar la misma clave. Mientras `register_attempt` permanezca como STUB, esta feature verifica el sobre, orden de entrega, registro único, propagación y rollback mediante un harness transaccional explícito; la creación, replay y reintento end-to-end se verifican en la feature que implemente el productor.
- **FR-026**: Conforme al principio constitucional de comunicación entre módulos, progreso, puntuación, racha y participación semanal reaccionan mediante receptores registrados por su propia app. Los productores futuros de `attempt_registered` y `session_completed` no conocen qué consumidores están activos; `gamification` conserva la propiedad exclusiva de las escrituras sobre `SeasonParticipation`.
- **FR-027**: El arranque de cada app consumidora DEBE registrar una sola vez únicamente los receptores de los eventos que consume. `learning` registra su receptor de progreso para `attempt_registered`; `gamification` registra sus receptores de puntuación, racha y participación para `attempt_registered`, y su receptor de participación para `session_completed`. La entrega de cada sobre DEBE poder verificarse con un receptor temporal sin implementar ninguna regla de negocio posterior.

### Shared Integration Contracts

- **FR-028**: La composición raíz DEBE incluir de forma definitiva los espacios de nombres `catalog`, `learning`, `gamification` y `analytics`, preservando las rutas existentes. Cada app DEBE exponer su propio agregador de rutas.
- **FR-029**: El agregador de `learning` DEBE incluir módulos separados y reservados para `enrollment`, `session`, `attempts` y `progress`. La misma separación DEBE reservarse para las áreas futuras que deban conectarse sin editar la composición raíz.
- **FR-030**: La plantilla base compartida DEBE ofrecer los bloques estables `title`, `main`, `sidebar`, `scripts` y `fragments`, conservar navegación semántica y mantener reglas o clases que produzcan foco visible durante la operación por teclado. Esta feature DEBE verificarlo mediante pruebas automatizadas rápidas sobre el HTML renderizado y los estilos aplicables, sin añadir automatización de navegador. Ninguna feature posterior de la línea base puede requerir cambios en esa plantilla para insertar su contenido.
- **FR-031**: La navegación DEBE obtener sus entradas de un registro distribuido por app. Las entradas conocidas de la línea base DEBEN poder reservarse desde esta feature y la plantilla de navegación NO DEBE necesitar cambios cuando se implemente una de ellas.
- **FR-032**: DEBEN quedar reservadas las carpetas de plantilla `catalog/content`, `learning/enrollment`, `learning/session`, `learning/attempts`, `learning/progress`, `gamification` y `analytics`, junto con carpetas de prueba equivalentes.
- **FR-033**: Las áreas `learning.views` y `learning.services` DEBEN ser paquetes. Sus archivos de inicialización DEBEN permanecer vacíos y sin reexportaciones para que las áreas paralelas trabajen en módulos distintos.
- **FR-034**: Tras integrar esta feature, `kronolearn/urls.py`, la plantilla base, los agregadores de rutas, el descubrimiento de navegación, los modelos, las migraciones y las definiciones de eventos DEBEN considerarse superficies bloqueadas para las seis features paralelas.

### Demonstration and Test Data

- **FR-035**: Una única operación `seed_demo` DEBE cargar de forma idempotente los tracks publicados "Crea tu registro de gastos con agentes y SDD" y "Fundamentos de negocio para equipos técnicos", al menos un módulo publicado por track, exactamente dos contenidos publicados en total con su versión vigente, un conjunto válido de opciones y un laboratorio por contenido, una cuenta learner, una cuenta content_admin y la temporada semanal vigente. Las dos cuentas DEBEN usar correos deterministas no personales bajo el dominio reservado `.invalid`, conservados únicamente en sus registros `Account` como identidad de acceso y clave natural de la carga.
- **FR-036**: Repetir `seed_demo` DEBE conservar las identidades lógicas y cantidades de todos sus registros, reparar únicamente datos demo incompletos que pueda identificar sin sobrescribir trabajo ajeno y no duplicar relaciones ni versiones.
- **FR-037**: `seed_demo` DEBE exigir confirmación explícita fuera de entornos de desarrollo. Cuando el modo de depuración no esté activo, NO DEBE crear cuentas con contraseñas conocidas ni revelar credenciales en salida, logs o auditoría.
- **FR-038**: DEBEN existir fábricas reutilizables para cada entidad añadida por esta feature y para las entidades existentes necesarias para construir sus relaciones. Cada fábrica DEBE producir por defecto un objeto válido y permitir variar los campos relevantes para pruebas de restricciones.

### Documentation and Ownership

- **FR-039**: `docs/contracts/domain-contracts.md` DEBE ser la fuente única de verdad para el diagrama de entidades, la firma y semántica exactas de cada servicio, los tipos de resultado, los contratos de eventos y sus reglas transaccionales.
- **FR-040**: El documento DEBE incluir una tabla de propiedad que asigne rutas no solapadas a autoría de contenido, inscripción, sesión diaria, intento y retroalimentación, ruta y progreso, y puntos y racha. También DEBE reservar rutas para liga semanal, métricas administrativas, insignias, repaso y meta semanal.
- **FR-041**: En aplicación del principio constitucional de propiedad de archivos y migraciones, la tabla DEBE identificar las superficies bloqueadas creadas aquí y registrar esta feature como propietaria de las migraciones de línea base en `catalog`, `learning` y `gamification`. Cualquier ampliación posterior se rige por el proceso constitucional de coordinación y aprobación.
- **FR-042**: Cada contrato STUB DEBE incluir una docstring que defina precondiciones, resultado, orden, ausencia de efectos, errores esperados, autorización futura e idempotencia cuando corresponda.

### Quality and Verification

- **FR-043**: Conforme al principio constitucional de idempotencia e integridad, las restricciones de persistencia específicas de esta feature DEBEN cubrir unicidad, límites por fila, relaciones, digests idempotentes y temporadas solapadas. Los invariantes agregados asignados explícitamente a una operación STUB, incluida la consecutividad de contenidos, se verifican como contrato y se aplicarán cuando se implemente su servicio propietario.
- **FR-044**: En aplicación del principio constitucional de contenido trazable y versionado, la frontera compartida de persistencia de esta feature DEBE aplicar la inmutabilidad a `ContentVersion`, sus `Choice` y su `LabExercise` antes de que exista la operación de publicación funcional.
- **FR-045**: Conforme al principio constitucional de privacidad por minimización, los correos `.invalid` de las cuentas demo solo PUEDEN persistirse en sus registros autoritativos `Account`; ninguna salida, log, auditoría, evento, agregado ni clasificación puede exponerlos. Ninguna de esas superficies puede conservar contraseñas, direcciones IP o tokens en claro, y toda referencia inválida registrable DEBE usar el resumen HMAC ya establecido por el proyecto.
- **FR-046**: La verificación DEBE cubrir la creación y aplicación completa de evoluciones, restricciones únicas y de integridad, inmutabilidad, límites de lunes y domingo, mapa de puntos, constantes de racha, entrega síncrona del evento y rollback mediante un harness transaccional, contratos STUB sin efectos, inspección automatizada de las entradas y propósitos de digest documentados, pruebas directas de determinismo y separación de propósito de `security_digest`, accesibilidad estructural automatizada e idempotencia de `seed_demo`. El uso runtime de los digests y las pruebas end-to-end de emisión, replay y reintento pertenecen a las features que implementen los productores.
- **FR-047**: En aplicación del principio constitucional de verificación obligatoria, la matriz de esta feature DEBE ejecutarse en SQLite y PostgreSQL; su guía de validación DEBE identificar cuáles casos de migración, concurrencia y auditoría requieren evidencia PostgreSQL.

### Acceptance Criteria by Requirement

- **AC-FR-001/002**: La revisión de rutas y comportamiento confirma que no aparece ninguna pantalla ni acción funcional nueva y que todos los flujos existentes de identidad y catálogo conservan sus resultados previos.
- **AC-FR-003/006-017**: Una instalación desde cero crea todas las entidades enumeradas; una matriz de casos válidos e inválidos confirma cardinalidad, unicidad, límites por fila, estados, relaciones, fechas, no solapamiento e inmutabilidad sin migraciones adicionales. `current_season` siempre devuelve la semana canónica correspondiente. La consecutividad de contenidos y las reglas agregadas de opciones se comprueban en el contrato del servicio futuro sin ejecutar lógica STUB. Al publicar una versión nueva en esa feature futura, solo cambia el número vigente de `ContentItem`; las versiones anterior y nueva conservan sus snapshots sin mutación, y exactamente una expone la bandera derivada de vigencia.
- **AC-FR-004/018-023**: La inspección automatizada encuentra todas las firmas, tipos y constantes exactos. Cada STUB produce `NotImplementedError` sin cambios persistentes y cada operación IMPLEMENTAR satisface sus casos vacíos, ordenamiento y concurrencia aplicables. La inspección de contratos y docstrings confirma las entradas canónicas y propósitos exactos de digest, y las pruebas directas de `security_digest` confirman determinismo y separación entre propósitos sin invocar productores STUB. El contrato de puntuación conserva la firma singular y especifica un único evento `attempt` cuyo monto suma los puntos de `RATING_POINTS` y el bono limitado por `STREAK_BONUS_CAP`; repetirlo no crea otro evento. Los dos tipos de métricas exponen los cuatro campos contractuales; por debajo del mínimo configurable indican supresión y devuelven `values` vacío, y una nueva clave documentada puede incorporarse sin alterar la firma.
- **AC-FR-024-027**: Un harness transaccional envía por separado `attempt_registered` y `session_completed`; receptores temporales reciben una vez sus argumentos nombrados y los receptores declarados no se registran dos veces al reiniciar apps. Una inspección confirma que `learning` se suscribe solo a `attempt_registered`, que `gamification` se suscribe a ambos eventos y que solo `gamification` escribe `SeasonParticipation`. No existe una dependencia directa desde los productores STUB hacia progreso o gamificación. Si un receptor de `attempt_registered` lanza una excepción, esta se propaga y el harness demuestra el rollback de sus escrituras y de los efectos anteriores. La prueba no invoca los productores STUB ni afirma creación, replay o reintento end-to-end antes de que sean implementados.
- **AC-FR-028-034**: Cada espacio de nombres resuelve sin colisiones, los módulos de rutas reservados se cargan, una plantilla de prueba puede sobrescribir los cinco bloques y una entrada de navegación puede declararse sin editar la plantilla ni la composición raíz. La salida renderizada conserva un elemento `nav` semántico y las reglas o clases de foco visible exigidas para operación por teclado.
- **AC-FR-035-038**: Dos ejecuciones consecutivas de la carga demo producen las mismas cantidades e identidades, incluidas exactamente una cuenta learner y una cuenta content_admin; la ejecución no confirmada fuera de desarrollo no cambia datos; todas las fábricas crean estados válidos y permiten provocar cada restricción.
- **AC-FR-039-042**: Una comparación automatizada entre documentación y código no encuentra firmas, tipos, estados ni propiedades ausentes; además, valida las seis filas de ownership de línea base, las cinco reservas de backlog y que ninguna pareja de features comparte una ruta editable.
- **AC-FR-043-047**: La matriz exigida se ejecuta en ambos entornos; la evidencia de producción equivalente demuestra evoluciones, restricciones, concurrencia y auditoría, y no aparecen secretos ni identificadores privados en salidas capturadas.

### Key Entities *(include if feature involves data)*

- **ContentItem**: Unidad editorial ordenada dentro de un módulo; controla estado y revisión y agrupa sus instantáneas publicadas.
- **ContentVersion**: Instantánea histórica e inmutable del contenido exacto que puede presentarse a un aprendiz.
- **Choice**: Respuesta posible y ordenada de una versión, con valoración y retroalimentación pedagógica.
- **LabExercise**: Actividad práctica opcional y única ligada a una versión concreta.
- **Enrollment**: Vínculo único entre una cuenta y un track que delimita todo su historial de aprendizaje.
- **Attempt**: Registro idempotente de una elección sobre la versión exacta presentada y de su condición puntuable.
- **Progress**: Agregado por inscripción y módulo para consultas de avance y precisión.
- **ScoreEvent**: Hecho idempotente que representa una concesión de puntos y su causa.
- **Streak**: Agregado por cuenta que conserva continuidad actual y máximo histórico.
- **WeeklySeason**: Intervalo calendario no solapado de lunes a domingo.
- **SeasonParticipation**: Agregado semanal por cuenta para clasificación y métricas.
- **AttemptResult**: Resultado inmutable que acompaña a un intento y transporta valoración, puntuabilidad y retroalimentación.
- **TrackProgress**: Proyección inmutable del avance total y por módulo de una inscripción.
- **LeaderboardEntry**: Proyección pública de una posición semanal con nombre visible y agregados, sin identidad privada.
- **ContentMetrics**: Proyección agregada reservada para métricas de contenido con reglas explícitas de supresión.
- **EngagementMetrics**: Proyección agregada reservada para actividad dentro de una ventana temporal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los seis equipos de la línea base pueden iniciar su feature desde el mismo punto y completar una prueba de importación y localización de contratos sin solicitar cambios en modelos, evoluciones, composición raíz o plantilla base.
- **SC-002**: Una integración simulada de las seis ramas, limitada a las rutas asignadas, produce cero conflictos en archivos compartidos y cero cambios fuera de la tabla de propiedad.
- **SC-003**: El 100% de las entidades, relaciones, restricciones, firmas, constantes y eventos enumerados tiene una comprobación automática que falla si el contrato desaparece o cambia.
- **SC-004**: En una instalación vacía, una persona puede cargar el entorno de demostración en menos de 2 minutos y repetir la carga sin crear ningún duplicado.
- **SC-005**: El 100% de los casos concurrentes de prueba para claves idempotentes y creación de temporada conserva un único resultado lógico y ningún estado parcial.
- **SC-006**: Una prueba automatizada traza las lecturas de las cinco features de backlog a contratos existentes y confirma que ninguna requiere cambios en entidades o firmas de línea base.
- **SC-007**: La misma matriz de aceptación obtiene un 100% de resultados satisfactorios en el entorno local ligero y en el entorno de almacenamiento equivalente a producción, con evidencia específica de evoluciones, concurrencia y auditoría en este último.
- **SC-008**: Una revisión automatizada encuentra cero contraseñas, direcciones IP, tokens o correos personales en los datos demo, y cero correos `.invalid` expuestos fuera de los dos registros autoritativos `Account`.
- **SC-009**: Una prueba automatizada valida las seis asignaciones de línea base contra el documento de contratos y confirma para cada una sus rutas editables, contratos consumidos y superficies bloqueadas.

## Assumptions

- La constitución vigente es la autoridad para reglas globales de dominio, autorización, privacidad, idempotencia, comunicación modular, tiempo, frontend, propiedad de archivos y verificación; esta spec solo concreta cómo se manifiestan en esta feature.
- `Account.display_name` ya existe y satisface el requisito de nombre visible; no se necesita una entidad de perfil ni una evolución en `accounts` salvo que la planificación detecte una ausencia real.
- Los estados de inscripción necesarios para la línea base son activa y retirada. La finalización se deriva y no se almacena como tercer estado.
- Las claves de idempotencia de intentos y eventos de puntuación son únicas globalmente para simplificar reintentos y correlación.
- El conjunto demo contiene un módulo por track y un contenido por módulo; ambos contenidos incluyen laboratorio para ejercitar la relación opcional sin ampliar el volumen mínimo.
- Insignias, repaso y meta semanal consumen intentos, progreso, eventos, rachas y participaciones como proyecciones calculadas. No se incluye propiedad persistente de insignias, agenda de repaso ni preferencias personalizadas de meta; cualquiera de esas necesidades requerirá una solicitud explícita de ampliación antes de implementar su feature.
- Los contratos de métricas definen tipos y semántica de retorno, pero no calculan ni muestran agregados en esta feature.
- Los nombres de archivos, módulos, firmas y bloques incluidos aquí son interfaces compartidas deliberadas y no decisiones internas intercambiables.
- La zona horaria fija del proyecto ya está configurada y es la única referencia para temporadas y fechas de actividad.

## Scope Boundaries

### In Scope

- Todas las entidades y evoluciones compartidas enumeradas.
- Firmas públicas definitivas, tipos de resultado, constantes y consultas marcadas para implementación.
- Definición de los eventos de intento y sesión completada, junto con el mecanismo de registro de receptores.
- Composición de rutas, bloques base, registro de navegación y estructura de carpetas reservada.
- Datos demo idempotentes y fábricas compartidas.
- Documento único de contratos y tabla de propiedad por feature.
- Pruebas de contrato, integridad, tiempo, señal, datos demo y compatibilidad de entornos.

### Out of Scope

- Cualquier interfaz o flujo funcional para aprendices o administradores.
- Implementar las reglas de autoría, inscripción, selección diaria, intento, retroalimentación, progreso, puntuación, racha, liga, métricas, insignias, repaso o meta semanal que están marcadas como STUB o reservadas.
- Generación de contenido mediante inteligencia artificial o ejecución de agentes dentro de la plataforma.
- Notificaciones externas, servicios adicionales, colas, workers, Redis o cron.
- Cambiar el comportamiento público existente de cuentas, roles, tracks, módulos, publicación, ordenamiento o auditoría.

## Dependencies

- La identidad existente aporta `Account`, sesiones, nombre visible y roles learner y content_admin.
- El catálogo existente aporta `Track`, `Module`, sus versiones publicadas, control de revisión, ordenamiento, desactivación y auditoría.
- La configuración del proyecto aporta una zona horaria fija y dos entornos de prueba: local ligero y equivalente a producción.
- Las seis features paralelas aceptan la tabla de propiedad y no modifican superficies bloqueadas sin una enmienda coordinada.
