# Feature Specification: Control de tema más sutil e integrado

**Feature Branch**: `010-subtle-theme-toggle`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "quiero que el botón de cambio de modo light/dark, sea más sutíl e integrado en la UI manteniendo el diseño brutalista"

## Clarifications

### Session 2026-08-22

- Q: ¿Qué tratamiento visual concreto debe tener el control de cambio de tema para que se sienta "más sutil e
  integrado" sin perder el lenguaje brutalista? → A: Solo ícono, sin texto visible permanente; el texto queda
  disponible como nombre accesible para lectores de pantalla y como confirmación visible al pasar el mouse o
  enfocar el control con teclado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Percibir el control como parte natural de la navegación (Priority: P1)

Como usuario de KronoLearn, quiero que el control de cambio de tema se vea como un ícono discreto integrado en la
navegación, en vez de un botón con caja, borde y sombra que compite visualmente con las acciones principales de la
página.

**Why this priority**: Es el cambio central solicitado; sin él, la feature no cumple su propósito de reducir el
peso visual del control actual.

**Independent Test**: Puede probarse abriendo cualquier página cubierta y comparando visualmente el control de
tema contra los botones de acción existentes (por ejemplo, "Guardar" o "Cerrar sesión"): el control de tema no debe
tener el borde ni la sombra dura que sí tienen esos botones.

**Acceptance Scenarios**:

1. **Given** un usuario ve la cabecera de cualquier página cubierta, **When** observa el control de tema, **Then**
   lo ve como un ícono sin borde ni sombra dura, con un peso visual similar al resto de la navegación (no como un
   botón de acción independiente).
2. **Given** un usuario pasa el mouse sobre el control o lo enfoca con teclado, **When** lo hace, **Then** aparece
   una confirmación textual visible de lo que hace el control, sin necesidad de activarlo primero.
3. **Given** el modo actual (claro u oscuro), **When** el usuario mira el ícono, **Then** el propio ícono (no solo
   el color) indica hacia qué modo cambiará al activarlo.

---

### User Story 2 - Mantener la identificación del control con tecnología de asistencia (Priority: P2)

Como usuario de un lector de pantalla, quiero que el control siga anunciando claramente su función y su estado
actual aunque ya no tenga un texto visible de forma permanente, para poder usarlo con la misma confianza que antes.

**Why this priority**: Sin esta garantía, simplificar el aspecto visual del control degradaría la accesibilidad ya
lograda en la versión anterior, lo cual viola una restricción explícita del sistema visual del proyecto.

**Independent Test**: Puede probarse navegando al control con un lector de pantalla (o inspeccionando su nombre
accesible), activándolo, y confirmando que el nombre y el estado anunciados cambian de forma coherente con el modo
resultante.

**Acceptance Scenarios**:

1. **Given** un usuario de lector de pantalla enfoca el control, **When** recibe el foco, **Then** el lector de
   pantalla anuncia un nombre accesible que describe la acción (por ejemplo, "Cambiar a modo oscuro") junto con su
   estado actual.
2. **Given** el usuario activa el control, **When** el modo cambia, **Then** el nombre accesible y el estado
   anunciado se actualizan para reflejar el nuevo modo (por ejemplo, ahora ofrece "Cambiar a modo claro").

---

### User Story 3 - No perder ninguna garantía ya lograda (Priority: P3)

Como usuario de la aplicación, quiero que este cambio puramente visual no afecte el tamaño mínimo de toque, el
foco visible, ni el comportamiento de persistencia y sincronización entre pestañas ya entregados, para no perder
funcionalidad ni accesibilidad a cambio de un diseño más discreto.

**Why this priority**: Es una garantía de no regresión más que una entrega de valor nueva; el valor principal ya
está cubierto por las historias 1 y 2.

**Independent Test**: Puede probarse repitiendo las pruebas de tamaño de toque, foco visible, persistencia y
sincronización entre pestañas ya definidas para el control, y confirmando que siguen cumpliéndose sin cambios.

**Acceptance Scenarios**:

1. **Given** un usuario en un dispositivo táctil, **When** toca el control, **Then** el área táctil sigue siendo
   al menos tan grande como la ya garantizada antes de este cambio (44×44px).
2. **Given** un usuario cambia el tema, **When** recarga la página o revisa otra pestaña abierta, **Then** la
   persistencia y la sincronización en tiempo real funcionan exactamente igual que antes de este cambio.

### Edge Cases

- ¿Qué pasa si el usuario nunca pasa el mouse ni enfoca el control (por ejemplo, en un dispositivo táctil, donde no
  existe "hover")? Debe poder reconocer la función del ícono por su forma (luna/sol), símbolos ampliamente
  entendidos, sin depender de haber visto la confirmación textual.
- ¿Qué pasa si el sistema o la fuente del usuario no puede representar el símbolo elegido? El control debe seguir
  siendo un elemento interactivo real, enfocable y con nombre accesible, aunque el símbolo visual no se muestre
  correctamente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El control de tema DEBE presentarse como un ícono sin caja: sin borde ni sombra dura visibles en su
  estado de reposo, a diferencia de los botones de acción (por ejemplo "Guardar", "Cerrar sesión").
- **FR-002**: El control NUNCA DEBE mostrar un texto visible de forma permanente junto al ícono; la descripción
  textual de la acción DEBE seguir disponible en todo momento como nombre accesible para tecnología de asistencia.
- **FR-003**: El sistema DEBE revelar una confirmación textual visible de la acción del control cuando un usuario
  lo enfoca con teclado o pasa el mouse sobre él, para que su propósito sea descubrible sin necesidad de activarlo
  primero.
- **FR-004**: El ícono DEBE cambiar de forma entre los dos estados (modo activo vs. modo al que cambiaría),
  nunca dependiendo solo del color para transmitir esa diferencia.
- **FR-005**: El control DEBE conservar el mismo tamaño mínimo de área táctil/clic ya garantizado antes de este
  cambio.
- **FR-006**: El control DEBE conservar el mismo indicador de foco visible ya exigido por las reglas de
  accesibilidad del sistema.
- **FR-007**: El nombre accesible y el estado anunciados a la tecnología de asistencia DEBEN actualizarse
  inmediatamente después de cada cambio de modo, reflejando el modo vigente.
- **FR-008**: Este cambio es puramente visual: NUNCA DEBE alterar el modo por defecto, la persistencia en el
  navegador, ni la sincronización en tiempo real entre pestañas ya entregadas.
- **FR-009**: El control DEBE seguir disponible exactamente en el mismo conjunto de páginas que antes de este
  cambio (toda la aplicación excepto el administrador de Django).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una revisión visual de la cabecera, el control de tema ya no se percibe como un botón con caja;
  se lee como parte de la navegación, cumpliendo el objetivo cualitativo de sentirse "más sutil e integrado".
- **SC-002**: El 100% de los usuarios que pasan el mouse o enfocan el control (sin hacer clic) pueden determinar,
  mediante el texto revelado, a qué modo cambiará.
- **SC-003**: Una revisión con lector de pantalla confirma que el nombre accesible y el estado se anuncian
  correctamente en ambos modos, con la misma paridad de accesibilidad ya exigida antes de este cambio.
- **SC-004**: El 100% de las pruebas automatizadas ya existentes sobre persistencia, sincronización entre
  pestañas y cobertura de páginas del control siguen pasando sin cambios tras este ajuste visual.

## Assumptions

- Esta feature es un refinamiento puramente visual del componente de cambio de tema entregado en
  `specs/009-dark-mode-toggle`; no cambia el mecanismo de aplicación del tema, la clave de almacenamiento en el
  navegador, ni la lógica de sincronización entre pestañas, que se dan por vigentes y correctos.
- El par de íconos luna/sol ya elegido en la feature anterior se asume suficientemente reconocible para esta
  presentación más minimalista; si la revisión visual durante la implementación revela que no lo es, elegir un par
  de íconos más claro es un detalle de implementación dentro del mismo componente, no una feature nueva.
- Revelar el texto al enfocar o pasar el mouse se asume suficiente para resolver la necesidad de "descubribilidad"
  planteada por el usuario; el mecanismo exacto (por ejemplo, un atributo nativo de tooltip u otro elemento visual)
  es una decisión técnica de la fase de planificación.
- El tratamiento sin caja (sin borde ni sombra) aplica únicamente a este control; ningún otro botón o componente
  existente cambia su tratamiento visual como parte de esta feature.
