# Feature Specification: Espacio de aprendizaje

**Feature Branch**: `007-learner-space`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Como aprendiz autenticado quiero una página que reúna los tracks en los que estoy inscrito, para retomar mi aprendizaje sin buscar dónde quedé."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retomar un track inscrito (Priority: P1)

Como aprendiz autenticado, quiero ver reunidos los tracks en los que estoy inscrito y entrar a la sesión del día de cualquiera de ellos para retomar mi aprendizaje sin buscar dónde quedé.

**Why this priority**: Este recorrido entrega el valor central de la feature: convierte el espacio de aprendizaje en el punto único desde el cual continuar los tracks propios.

**Independent Test**: Una cuenta activa inscrita en dos tracks abre `/learn/`, ve únicamente esos dos tracks con su título y cantidad de módulos, y puede ir desde cada uno a su sesión del día.

**Acceptance Scenarios**:

1. **Given** una cuenta activa inscrita en uno o más tracks, **When** abre `/learn/`, **Then** ve una entrada por cada track propio con su título y su cantidad de módulos.
2. **Given** un track mostrado en el espacio de aprendizaje, **When** el aprendiz elige continuar, **Then** llega directamente a la sesión del día correspondiente a ese track.
3. **Given** una cuenta inscrita en varios tracks, **When** abre `/learn/`, **Then** puede distinguir cada track y elegir de forma independiente cuál retomar.

---

### User Story 2 - Descubrir qué hacer sin inscripciones (Priority: P2)

Como aprendiz autenticado sin inscripciones, quiero encontrar una orientación clara para explorar el catálogo y poder comenzar una ruta de aprendizaje.

**Why this priority**: Sin este estado, una cuenta nueva encontraría un espacio vacío sin un siguiente paso útil.

**Independent Test**: Una cuenta activa sin inscripciones abre `/learn/`, ve un estado vacío comprensible y puede llegar al catálogo mediante la acción ofrecida.

**Acceptance Scenarios**:

1. **Given** una cuenta activa sin inscripciones, **When** abre `/learn/`, **Then** ve un estado vacío que explica que todavía no tiene tracks inscritos.
2. **Given** el estado vacío, **When** el aprendiz elige explorar el catálogo, **Then** llega al catálogo para consultar los tracks disponibles.

---

### User Story 3 - Mantener privado el espacio personal (Priority: P3)

Como aprendiz, quiero que mi espacio de aprendizaje muestre solo mis inscripciones y permanezca reservado a cuentas activas para que otra persona no pueda conocer ni usar mi recorrido.

**Why this priority**: El listado reúne información personal de aprendizaje; el aislamiento entre cuentas y el control de acceso deben conservarse aunque cambie el contenido de la página.

**Independent Test**: Se preparan dos cuentas activas con inscripciones diferentes, se abre `/learn/` con cada una y se confirma que ninguna ve los tracks exclusivos de la otra; una persona sin sesión es dirigida al acceso.

**Acceptance Scenarios**:

1. **Given** dos cuentas activas con inscripciones distintas, **When** una de ellas abre `/learn/`, **Then** ve solo los tracks en los que esa cuenta está inscrita.
2. **Given** una persona sin sesión iniciada, **When** intenta abrir `/learn/`, **Then** es dirigida al inicio de sesión y se conserva `/learn/` como destino solicitado.
3. **Given** una cuenta que no está activa, **When** intenta abrir `/learn/`, **Then** no recibe el espacio de aprendizaje.
4. **Given** una cuenta activa que inicia sesión correctamente, **When** termina el proceso de acceso, **Then** aterriza en `/learn/`.

### Edge Cases

- Si un track inscrito no contiene módulos, debe mostrarse con una cantidad de cero módulos sin inventar progreso ni ocultar las demás inscripciones.
- Si dos tracks tienen el mismo título, cada entrada debe conservar su propia acción hacia la sesión correspondiente sin mezclarlas.
- Si la cuenta pierde su estado activo entre el inicio de sesión y la consulta de `/learn/`, no debe recibir información de sus inscripciones.
- Si no existen inscripciones propias pero sí de otras cuentas, debe mostrarse el estado vacío y no información ajena.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ofrecer en `/learn/` el espacio de aprendizaje personal para cuentas activas con sesión iniciada.
- **FR-002**: El espacio de aprendizaje DEBE mostrar exactamente una entrada por cada track en el que la cuenta en sesión está inscrita.
- **FR-003**: Cada entrada de track DEBE mostrar su título y la cantidad total de módulos que contiene.
- **FR-004**: Cada entrada de track DEBE ofrecer una acción operable que lleve directamente a la sesión del día de ese mismo track.
- **FR-005**: El sistema DEBE excluir del espacio de aprendizaje todas las inscripciones que pertenezcan a otras cuentas.
- **FR-006**: Cuando la cuenta no tenga inscripciones propias, el espacio DEBE mostrar un estado vacío comprensible con una acción operable para explorar el catálogo.
- **FR-007**: Una persona sin sesión iniciada que solicite `/learn/` DEBE ser dirigida al inicio de sesión conservando `/learn/` como destino solicitado.
- **FR-008**: Una cuenta que no esté activa NO DEBE poder consultar el espacio de aprendizaje.
- **FR-009**: Un inicio de sesión exitoso DEBE continuar llevando a la cuenta a `/learn/`.
- **FR-010**: El espacio de aprendizaje NO DEBE mostrar porcentaje de progreso, puntos, racha, recomendaciones ni resúmenes calculados.
- **FR-011**: Esta especificación DEBE observar los principios aplicables 4, 6, 9, 11, 12, 13 y 14 de la constitución vigente sobre seguridad, verificación, entrega incremental, accesibilidad, autorización, privacidad y fronteras entre módulos, sin redefinir sus reglas globales.

### Acceptance Criteria by Requirement

- **AC-FR-001-004**: Una cuenta activa con varias inscripciones abre `/learn/` y encuentra una entrada por cada track propio, cada una con el título, el conteo de módulos y una acción que abre la sesión del día del track elegido.
- **AC-FR-005**: Dos cuentas con inscripciones distintas consultan por separado `/learn/` y ninguna respuesta contiene tracks inscritos únicamente por la otra cuenta.
- **AC-FR-006**: Una cuenta sin inscripciones abre `/learn/`, ve el estado vacío y puede llegar al catálogo mediante su acción principal.
- **AC-FR-007-009**: Las comprobaciones de acceso confirman que una persona anónima es dirigida al inicio de sesión con `/learn/` como destino, una cuenta inactiva no accede y una cuenta activa que inicia sesión aterriza en `/learn/`.
- **AC-FR-010**: La inspección del espacio con y sin inscripciones confirma que no aparecen porcentajes de progreso, puntos, rachas, recomendaciones ni otros resúmenes calculados.
- **AC-FR-011**: La revisión de conformidad confirma el aislamiento por cuenta, la protección para cuentas activas, la ausencia de datos privados ajenos y la operación mediante teclado sin depender únicamente del color.

### Key Entities

- **Aprendiz**: Cuenta activa que consulta su espacio personal; su identidad determina qué inscripciones pueden presentarse.
- **Inscripción**: Relación entre un aprendiz y un track que habilita la aparición de ese track en su espacio de aprendizaje.
- **Track**: Ruta de aprendizaje inscrita; para esta feature aporta su título, su conjunto de módulos y el destino de su sesión del día.
- **Módulo**: Agrupación de contenido dentro de un track; en esta feature solo interviene en el conteo total mostrado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las inscripciones propias aparece una sola vez en el espacio de aprendizaje con el título y el conteo de módulos correctos.
- **SC-002**: El 100% de los tracks mostrados permite llegar a su sesión del día en una sola acción desde `/learn/`.
- **SC-003**: En una validación con cinco aprendices, al menos cuatro pueden identificar un track inscrito y comenzar su sesión del día en 30 segundos o menos, sin ayuda.
- **SC-004**: El 100% de las cuentas sin inscripciones de la prueba encuentra el estado vacío y puede llegar al catálogo en una sola acción.
- **SC-005**: En el 100% de las comprobaciones entre cuentas, ninguna persona ve un track inscrito exclusivamente por otra cuenta.
- **SC-006**: El 100% de las comprobaciones de acceso impide que personas anónimas o cuentas inactivas reciban información del espacio de aprendizaje.
- **SC-007**: Al menos el 95% de las consultas realizadas bajo condiciones normales muestra el listado o el estado vacío en dos segundos o menos.
- **SC-008**: El 100% de las acciones principales del espacio puede localizarse y activarse usando únicamente el teclado.

## Assumptions

- Las cuentas, la autenticación y el control de estado activo ya existen y conservan su comportamiento vigente.
- Las inscripciones, los tracks, sus módulos y las sesiones del día ya existen y están disponibles para consulta mediante las capacidades publicadas del producto.
- El catálogo ya existe y está disponible como destino del estado vacío.
- La cantidad de módulos corresponde al total actual de módulos asociados al track, incluida una cantidad de cero cuando corresponda.
- Esta feature presenta las inscripciones existentes; crear o cancelar una inscripción pertenece a otros recorridos.

## Scope Boundaries

### In Scope

- Listado de tracks en los que está inscrita la cuenta en sesión.
- Título y cantidad de módulos de cada track inscrito.
- Acceso directo a la sesión del día de cada track mostrado.
- Estado vacío con acceso al catálogo.
- Aislamiento de inscripciones entre cuentas.
- Conservación del acceso exclusivo para cuentas activas y del destino posterior al inicio de sesión.

### Out of Scope

- Porcentaje de progreso.
- Puntos y rachas.
- Recomendaciones.
- Cualquier resumen calculado del aprendizaje.
- Creación o cancelación de inscripciones.
- Cambios en la autenticación, en el estado de las cuentas, en el catálogo o en la sesión del día.

## Dependencies

- Deben existir inscripciones que relacionen las cuentas con los tracks correspondientes.
- Los tracks deben aportar un título, sus módulos y un destino vigente para la sesión del día.
- El catálogo debe permanecer disponible como siguiente paso para una cuenta sin inscripciones.
- Los controles existentes de sesión y cuenta activa deben permanecer disponibles para proteger `/learn/`.
- El proceso de inicio de sesión debe conservar `/learn/` como destino exitoso.

## Constraints

- El espacio debe limitarse a presentar datos disponibles de las inscripciones y los tracks; no debe calcular métricas de progreso ni gamificación.
- La identidad usada para seleccionar inscripciones debe ser la de la cuenta en sesión y nunca una identidad proporcionada por la persona en la solicitud.
- La ausencia de inscripciones propias no puede revelar la existencia de inscripciones pertenecientes a otras cuentas.