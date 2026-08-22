# Feature Specification: Cambio entre modo claro y modo oscuro

**Feature Branch**: `009-dark-mode-toggle`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Como usuario quiero tener la posibilidad de cambiar entre el light mode (default) y dark mode (nuevo)"

## Clarifications

### Session 2026-08-22

- Q: Si un usuario tiene la aplicación abierta en dos pestañas del mismo navegador y cambia el tema en una, ¿la otra
  pestaña debe actualizarse automáticamente en tiempo real, o basta con que muestre el nuevo tema la próxima vez que
  se recargue o navegue en ella? → A: Tiempo real en todas las pestañas abiertas del mismo navegador.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Activar el modo oscuro (Priority: P1)

Como usuario de KronoLearn, quiero cambiar la apariencia de la aplicación de modo claro (el actual, por defecto) a
modo oscuro, para poder usar la plataforma con menor fatiga visual en entornos de poca luz o según mi preferencia
personal.

**Why this priority**: Es la funcionalidad central solicitada; sin ella no existe la feature. Sin este cambio, todo
lo demás (persistencia, alcance en otras páginas) no tiene sentido.

**Independent Test**: Puede probarse por completo abriendo cualquier página cubierta por la feature, activando el
control de tema, y confirmando que la apariencia visual cambia de claro a oscuro sin recargar la funcionalidad ni
perder datos en pantalla.

**Acceptance Scenarios**:

1. **Given** un usuario visualiza una página en modo claro (el estado por defecto), **When** activa el control de
   cambio de tema, **Then** la página se muestra en modo oscuro manteniendo el mismo contenido y funcionalidad.
2. **Given** un usuario tiene el modo oscuro activo, **When** activa el control de cambio de tema nuevamente,
   **Then** la página vuelve al modo claro.
3. **Given** un usuario cambia de tema, **When** el cambio ocurre, **Then** todos los estados visuales (éxito, error,
   advertencia, selección, foco) permanecen distinguibles y perceptibles sin depender únicamente del color.

---

### User Story 2 - Conservar la preferencia de tema en el navegador (Priority: P2)

Como usuario que ya eligió modo oscuro (o volvió a modo claro), quiero que la aplicación recuerde mi elección en este
navegador, para no tener que volver a activarla cada vez que visito o recargo la aplicación.

**Why this priority**: Sin recordar la preferencia, el usuario tendría que re-activarla en cada página o visita, lo
que degrada seriamente la experiencia aunque el cambio de tema en sí (User Story 1) ya funcione.

**Independent Test**: Puede probarse activando el modo oscuro, recargando la página o navegando a otra página
cubierta por la feature, y confirmando que el modo oscuro se mantiene sin necesidad de volver a activarlo.

**Acceptance Scenarios**:

1. **Given** un usuario activó el modo oscuro en este navegador, **When** recarga la página o navega a otra página
   cubierta por la feature, **Then** la página se muestra en modo oscuro sin que el usuario deba volver a activarlo.
2. **Given** un usuario nunca ha elegido un tema en este navegador, **When** visita la aplicación por primera vez,
   **Then** la aplicación se muestra en modo claro (el valor por defecto).
3. **Given** un usuario activó el modo oscuro en un navegador o dispositivo, **When** accede desde un navegador o
   dispositivo distinto (incluso con la misma cuenta), **Then** ve el modo claro por defecto, ya que la preferencia
   no se sincroniza entre dispositivos.
4. **Given** un usuario tiene la aplicación abierta en dos o más pestañas del mismo navegador, **When** cambia el
   tema en una de ellas, **Then** el resto de pestañas abiertas se actualiza al nuevo tema automáticamente, sin
   necesidad de recargarlas ni navegar en ellas.

---

### User Story 3 - Disponibilidad del control en toda la aplicación (Priority: P3)

Como usuario, quiero encontrar el control para cambiar de tema de forma consistente en cualquier página de la
aplicación (autenticada o no), para no tener que buscarlo o perder mi elección al navegar entre secciones.

**Why this priority**: Mejora la consistencia y previsibilidad de la experiencia, pero la feature ya aporta valor
completo con el cambio de tema (User Story 1) y su persistencia (User Story 2) disponibles aunque sea en un único
punto de entrada inicial.

**Independent Test**: Puede probarse navegando por login, registro y las páginas del área de aprendiz (inicio,
catálogo, sesión diaria, progreso) y confirmando que el control de tema está presente y funciona igual en todas
ellas, y que el tema elegido se mantiene al navegar entre secciones.

**Acceptance Scenarios**:

1. **Given** un usuario está en cualquier página pública o autenticada de la aplicación (excluyendo el
   administrador de Django), **When** busca el control de cambio de tema, **Then** lo encuentra en una ubicación
   consistente y predecible.
2. **Given** un usuario cambia de tema en una página, **When** navega a otra página de la aplicación, **Then** el
   tema elegido se mantiene sin necesidad de volver a activarlo.

### Edge Cases

- ¿Qué pasa si el navegador del usuario tiene JavaScript deshabilitado? La aplicación debe seguir siendo usable en
  modo claro (el valor por defecto); el control de cambio de tema puede no estar disponible en ese caso.
- ¿Qué pasa si el usuario borra los datos de navegación o usa una ventana privada/incógnito? La preferencia se
  pierde y la aplicación vuelve a mostrarse en modo claro, igual que en la primera visita.
- ¿Qué pasa si un componente visual nuevo o existente no tiene aún un estilo definido para modo oscuro? El
  componente no debe usarse en producción sin su equivalente oscuro definido; no debe romper el layout ni volverse
  ilegible.
- ¿Qué pasa con contenido embebido o generado por el administrador (por ejemplo HTML enriquecido en microlecciones)
  que asuma fondo claro? Debe seguir siendo legible en modo oscuro; los casos que no puedan garantizarlo quedan
  fuera del alcance de esta feature y se documentan como limitación conocida.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ofrecer un control visible e identificable que permita al usuario alternar entre modo
  claro y modo oscuro en cualquier página cubierta por la feature.
- **FR-002**: El sistema DEBE mostrar el modo claro como apariencia por defecto para cualquier usuario o navegador
  que no haya elegido previamente un tema.
- **FR-003**: El sistema DEBE aplicar el modo oscuro a la totalidad de la interfaz visible de la página activa
  (fondo, texto, bordes, componentes reutilizables y estados visuales), sin dejar zonas o componentes que
  permanezcan forzados en la apariencia contraria.
- **FR-004**: El sistema DEBE recordar la última elección de tema del usuario en el navegador actual y aplicarla
  automáticamente en visitas y recargas posteriores desde ese mismo navegador.
- **FR-005**: El sistema DEBE aplicar el tema elegido de manera consistente en login, registro, y todas las páginas
  del área de aprendiz (inicio, catálogo, sesión diaria, progreso); el administrador de Django queda fuera del
  alcance y conserva su apariencia estándar.
- **FR-006**: En modo oscuro, ningún estado visual (éxito, error, advertencia, información, selección, foco) DEBE
  distinguirse únicamente por el color; debe conservar el mismo indicador adicional (ícono, texto o borde) que en
  modo claro.
- **FR-007**: El sistema DEBE mantener en modo oscuro los mismos requisitos de accesibilidad ya exigidos en modo
  claro: foco visible en todo elemento interactivo, área mínima de toque, contraste suficiente de texto sobre fondo,
  y respeto de `prefers-reduced-motion`.
- **FR-008**: El cambio de tema NUNCA DEBE alterar, ocultar o invalidar datos de dominio en pantalla (progreso,
  puntuación, respuestas seleccionadas, formularios en curso); es un cambio puramente de apariencia.
- **FR-009**: El sistema DEBE propagar en tiempo real un cambio de tema a todas las demás pestañas o ventanas
  abiertas del mismo navegador para la aplicación, sin requerir que el usuario las recargue o navegue en ellas.

### Key Entities

- **Preferencia de tema**: valor con dos estados posibles (claro/oscuro) asociado al navegador del usuario actual.
  No se asocia a la cuenta del usuario ni se almacena en el servidor; no es un dato de dominio ni de negocio.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede cambiar entre modo claro y modo oscuro en menos de 2 segundos desde cualquier página
  cubierta por la feature, sin recargar manualmente ni perder su posición en la página.
- **SC-002**: El 100% de los componentes visuales reutilizables definidos en el sistema visual de KronoLearn se ven
  correctamente (sin texto ilegible, sin estados indistinguibles, sin roturas de layout) tanto en modo claro como en
  modo oscuro.
- **SC-003**: Un usuario que eligió modo oscuro lo sigue viendo activo en el 100% de sus visitas posteriores desde el
  mismo navegador, sin necesidad de volver a activarlo, hasta que borre los datos de navegación o cambie de
  navegador/dispositivo.
- **SC-004**: Ninguna página cubierta por la feature presenta, en modo oscuro, un contraste de texto sobre fondo por
  debajo de los mínimos de accesibilidad ya exigidos en modo claro.
- **SC-005**: Al cambiar de tema en una pestaña, el 100% de las demás pestañas abiertas del mismo navegador para la
  aplicación reflejan el nuevo tema en menos de 1 segundo, sin intervención del usuario en ellas.

## Assumptions

- El modo claro definido por el sistema visual actual (`.github/instructions/design.instructions.md`) se conserva
  sin cambios como apariencia por defecto; esta feature únicamente añade una apariencia oscura alternativa y el
  control para elegirla.
- La preferencia de tema es una configuración de presentación del navegador, no un dato de dominio del usuario; por
  eso se guarda únicamente en el dispositivo/navegador actual (ver decisión de alcance) y no requiere autenticación
  ni cambios en el modelo de cuenta.
- La aplicación no adapta el tema automáticamente según la preferencia del sistema operativo (`prefers-color-scheme`)
  al primer ingreso; todo usuario nuevo ve modo claro hasta que elige explícitamente modo oscuro.
- El administrador de Django (`/admin/`) no forma parte del alcance de esta feature y conserva su apariencia
  estándar, según lo acordado en la decisión de alcance.
- Definir los tokens visuales concretos del modo oscuro (colores, contrastes) es responsabilidad de la fase de
  planificación técnica y debe ampliar `.github/instructions/design.instructions.md` como fuente de verdad del
  sistema visual, conforme al principio constitucional de frontend accesible.
