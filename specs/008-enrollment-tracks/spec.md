# Feature Specification: Exploración e inscripción en tracks

**Feature Branch**: `008-enrollment-tracks`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Como aprendiz quiero explorar los tracks disponibles e inscribirme en uno, para empezar una ruta de aprendizaje."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explorar el catálogo de tracks disponibles (Priority: P1)

Como aprendiz, quiero ver los tracks disponibles con su título, su descripción y su cantidad de módulos, y poder abrir el detalle de cada uno, para decidir en cuál inscribirme.

**Why this priority**: Sin poder explorar el catálogo, un aprendiz no tiene información suficiente para elegir un track, lo que bloquea cualquier inscripción posterior.

**Independent Test**: Un aprendiz autenticado abre el catálogo, ve la lista de tracks disponibles con sus datos básicos y abre el detalle de uno sin necesidad de inscribirse.

**Acceptance Scenarios**:

1. **Given** un aprendiz autenticado, **When** abre el catálogo, **Then** ve cada track disponible con su título, su descripción y su cantidad de módulos.
2. **Given** un aprendiz autenticado, **When** abre el detalle de un track disponible, **Then** ve su información completa.
3. **Given** un track retirado, **When** el aprendiz explora el catálogo, **Then** no lo ve listado entre los tracks disponibles.

---

### User Story 2 - Inscribirse en un track (Priority: P1)

Como aprendiz, quiero inscribirme en un track disponible, para empezar una ruta de aprendizaje.

**Why this priority**: Es la acción central de la feature; sin una inscripción registrada no existe ruta de aprendizaje que retomar en ninguna otra pantalla.

**Independent Test**: Un aprendiz envía la inscripción a un track disponible y queda registrado como inscrito, verificable consultando únicamente sus propias inscripciones.

**Acceptance Scenarios**:

1. **Given** un aprendiz autenticado y un track disponible, **When** se inscribe, **Then** queda registrada exactamente una inscripción para ese aprendiz en ese track.
2. **Given** un aprendiz ya inscrito en un track, **When** envía la inscripción una segunda vez, **Then** sigue teniendo una sola inscripción en ese track y no ve ningún error.
3. **Given** dos aprendices distintos, **When** cada uno se inscribe en el mismo track, **Then** cada uno obtiene su propia inscripción independiente.

---

### User Story 3 - Rechazo uniforme ante tracks no disponibles (Priority: P2)

Como aprendiz, al intentar inscribirme en un track retirado o inexistente, quiero recibir la misma respuesta de rechazo en ambos casos, para no quedar en un estado ambiguo.

**Why this priority**: Protege la integridad de las inscripciones y evita distinguir entre un track retirado y uno inexistente; es necesaria para un flujo robusto pero depende de que la inscripción básica (US2) ya exista.

**Independent Test**: Un aprendiz intenta inscribirse en un identificador de track inexistente y, por separado, en uno retirado; ambas peticiones producen la misma respuesta y ninguna crea una inscripción.

**Acceptance Scenarios**:

1. **Given** un track retirado, **When** el aprendiz intenta inscribirse, **Then** recibe una respuesta de rechazo y no se crea ninguna inscripción.
2. **Given** un identificador de track inexistente, **When** el aprendiz intenta inscribirse, **Then** recibe la misma respuesta de rechazo que ante un track retirado.

---

### Edge Cases

- Un aprendiz no puede ver las inscripciones de otra persona bajo ninguna circunstancia.
- Un aprendiz no puede crear una inscripción a nombre de otra cuenta.
- Dos envíos de inscripción al mismo track prácticamente simultáneos no producen más de una inscripción registrada.
- Una persona sin sesión iniciada que intenta explorar el catálogo o inscribirse es dirigida al inicio de sesión en vez de recibir el catálogo o crear una inscripción.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST mostrar la lista de tracks disponibles (no retirados) con su título, su descripción y su cantidad de módulos.
- **FR-002**: Los aprendices MUST poder abrir el detalle de cualquier track disponible.
- **FR-003**: El sistema MUST permitir que un aprendiz autenticado se inscriba en un track disponible.
- **FR-004**: El sistema MUST garantizar como máximo una inscripción por cada par aprendiz-track, sin importar cuántas veces se envíe la solicitud.
- **FR-005**: Un envío repetido de inscripción al mismo track MUST devolver el mismo estado de éxito, sin crear una segunda inscripción ni mostrar un error.
- **FR-006**: El sistema MUST rechazar los intentos de inscripción en un track retirado.
- **FR-007**: El sistema MUST rechazar los intentos de inscripción en un identificador de track inexistente.
- **FR-008**: La respuesta de rechazo para un track retirado y para uno inexistente MUST ser indistinguible entre sí.
- **FR-009**: El sistema MUST restringir la visualización de inscripciones a las de la cuenta autenticada.
- **FR-010**: El sistema MUST impedir que una cuenta cree inscripciones para cualquier otra cuenta.
- **FR-011**: Explorar el catálogo e inscribirse MUST requerir una cuenta autenticada y activa.

### Key Entities

- **Track**: ruta de aprendizaje publicada, con título, descripción y cantidad de módulos; puede estar disponible o retirado.
- **Inscripción (Enrollment)**: relación entre un aprendiz y un track, única por cada par aprendiz-track, marca el inicio de su ruta de aprendizaje en ese track.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un aprendiz puede ver la lista completa de tracks disponibles, con título, descripción y cantidad de módulos, en una sola pantalla.
- **SC-002**: El 100% de los envíos duplicados de inscripción al mismo track por el mismo aprendiz resulta en exactamente una inscripción registrada.
- **SC-003**: El 100% de los intentos de inscripción en tracks retirados o inexistentes recibe la misma respuesta de rechazo.
- **SC-004**: El 0% de los aprendices puede ver o crear inscripciones que no sean propias.
- **SC-005**: Un aprendiz nuevo puede pasar de explorar el catálogo a tener una inscripción activa en tres pasos: ver el catálogo, abrir el detalle y confirmar la inscripción.

## Assumptions

- El catálogo de tracks (título, descripción, cantidad de módulos y estado disponible/retirado) ya existe como parte del contenido publicado por specs previas.
- La autenticación y la verificación de cuenta activa ya están resueltas por la app de cuentas existente y se reutilizan tal cual.
- "Track disponible" equivale a un track publicado y no retirado; el estado de retiro ya es un atributo existente del catálogo.
- La baja de una inscripción, la inscripción masiva, las invitaciones, los tracks privados y la recomendación automática de tracks quedan fuera de esta feature.
