# Feature Specification: Autenticacion y perfil

**Feature Branch**: `002-user-auth-profile`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "Como persona interesada en aprender, quiero registrarme e iniciar y cerrar sesion para acceder de forma segura a mi experiencia de aprendizaje. El usuario puede crear una cuenta con datos minimos y contrasena; iniciar y cerrar sesion; recibe el rol de aprendiz por defecto; solo un administrador autorizado puede asignar el rol de administrador de contenido; las rutas privadas redirigen a autenticacion; y una cuenta no puede consultar informacion privada de otra. Dependencias: ninguna."

## Clarifications

### Session 2026-08-20

- Q: ¿Que tipo de cuenta puede asignar o retirar el rol de administrador de contenido? → A: Solo un administrador de plataforma.
- Q: ¿Una cuenta conserva el rol de aprendiz cuando recibe el rol de administrador de contenido? → A: Si, conserva aprendiz y añade administrador de contenido.
- Q: ¿Como debe responder el sistema ante intentos repetidos de inicio de sesion con credenciales invalidas? → A: Aplicar una espera progresiva sin revelar si la cuenta existe.
- Q: ¿A donde debe dirigirse una persona despues de autenticarse tras intentar acceder a una ruta privada? → A: Volver a la ruta interna solicitada; usar el inicio del aprendiz si el destino no es valido.
- Q: ¿Que historial debe conservarse de los intentos de asignar o retirar el rol de administrador de contenido? → A: Registrar actor, cuenta afectada, accion, resultado y fecha de todos los intentos.
- Q: ¿Que historial debe conservarse cuando alguien intenta cambiar el rol usando el identificador de una cuenta que no existe? → A: Auditar todo intento autenticado; dejar la cuenta objetivo sin asociar y conservar una referencia no reversible del identificador solicitado.
- Q: ¿Como debe comprobarse que una cuenta no puede acceder al perfil de otra si la ruta del perfil no contiene ningun identificador? → A: Mantener una unica ruta de perfil propio; probar dos sesiones e ignorar cualquier identificador de cuenta adicional.
- Q: ¿Puede un administrador de plataforma asignarse o retirarse a si mismo el rol de administrador de contenido? → A: No; denegar la operacion, no cambiar roles y auditarla como denegada con actor igual a objetivo.
- Q: ¿Deben auditarse los intentos autenticados de cambiar un rol cuando el identificador de cuenta incluido en la ruta no tiene un formato UUID valido? → A: Si; auditar como objetivo inexistente con una referencia no reversible, informar que no se encontro al administrador autorizado y responder con una denegacion generica a los demas actores.
- Q: ¿Que protocolo debe usarse para comprobar que al menos el 90% completa el registro e identifica correctamente el inicio y cierre de sesion? → A: Diez participantes representativos realizan sin asistencia el registro, primer inicio y cierre de sesion; al menos nueve completan el flujo en menos de tres minutos e identifican correctamente ambos estados.
- Q: ¿Que objetivo medible deben cumplir las respuestas interactivas ordinarias en el entorno de aceptacion? → A: No fijar un objetivo de latencia en esta feature; definirlo despues de obtener una linea base operativa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear una cuenta e iniciar sesion (Priority: P1)

Como persona interesada en aprender, quiero crear una cuenta con los datos imprescindibles e iniciar sesion para acceder a una experiencia de aprendizaje asociada a mi identidad.

**Why this priority**: Es la puerta de entrada al flujo principal de aprendizaje y aporta valor aun sin funciones administrativas ni edicion de perfil.

**Independent Test**: Una persona sin cuenta puede registrarse con correo electronico, nombre visible y contrasena, comprobar que recibe el rol de aprendiz e iniciar sesion con las credenciales creadas.

**Acceptance Scenarios**:

1. **Given** una persona sin cuenta y un correo electronico no registrado, **When** proporciona correo electronico, nombre visible y una contrasena que cumple la politica comunicada, **Then** el sistema crea una unica cuenta con rol de aprendiz.
2. **Given** una cuenta activa, **When** la persona presenta credenciales validas, **Then** inicia una sesion autenticada y puede continuar hacia su experiencia de aprendizaje.
3. **Given** una cuenta activa, **When** la persona presenta credenciales invalidas, **Then** no inicia sesion y recibe un mensaje que no revela si el correo o la contrasena fue el dato incorrecto.
4. **Given** un correo electronico ya asociado a una cuenta, **When** otra persona intenta registrarlo, **Then** el sistema rechaza la creacion duplicada y ofrece una respuesta segura para continuar con una cuenta existente.
5. **Given** intentos repetidos de inicio de sesion con credenciales invalidas, **When** continuan los intentos desde la misma cuenta declarada o el mismo origen, **Then** el sistema aplica esperas progresivas y mantiene una respuesta que no confirma si la cuenta existe.
6. **Given** una persona redirigida a autenticacion desde una ruta privada interna, **When** inicia sesion correctamente, **Then** vuelve a la ruta solicitada si sigue siendo interna, valida y autorizada; en caso contrario, llega al inicio del aprendiz.

---

### User Story 2 - Proteger la sesion y el perfil propio (Priority: P2)

Como aprendiz, quiero acceder solo a mi perfil y cerrar sesion para mantener privada mi informacion personal cuando dejo de usar el servicio.

**Why this priority**: Convierte la cuenta en un espacio privado y cumple el principio de seguridad por defecto exigido por el proyecto.

**Independent Test**: Con dos cuentas de aprendiz, cada persona puede consultar su propio perfil, ninguna puede consultar el de la otra y una sesion cerrada deja de permitir acceso a rutas privadas.

**Acceptance Scenarios**:

1. **Given** una persona no autenticada que solicita una ruta privada, **When** intenta acceder, **Then** es redirigida a autenticacion y no se muestra contenido privado.
2. **Given** una persona autenticada, **When** consulta su perfil, **Then** ve exclusivamente los datos privados asociados a su propia cuenta.
3. **Given** dos cuentas distintas, **When** cada una solicita su perfil o aporta el identificador de la otra como dato adicional, **Then** el sistema ignora ese identificador y consulta o modifica exclusivamente el perfil asociado a la sesion actual, sin revelar ni cambiar informacion ajena.
4. **Given** una persona autenticada, **When** cierra sesion, **Then** su sesion deja de ser valida y cualquier acceso posterior a una ruta privada exige autenticarse de nuevo.
5. **Given** una persona autenticada, **When** actualiza su nombre visible con un valor valido, **Then** el perfil propio refleja el cambio sin alterar su correo, contrasena ni rol.

---

### User Story 3 - Administrar roles de contenido (Priority: P3)

Como administrador de plataforma, quiero asignar o retirar el rol de administrador de contenido para delegar la gestion editorial sin permitir que una cuenta eleve sus propios privilegios.

**Why this priority**: Habilita la futura administracion de contenido, pero no es necesaria para que un aprendiz cree y use su cuenta.

**Independent Test**: Un administrador de plataforma puede asignar y retirar el rol de administrador de contenido a otra cuenta, mientras que una cuenta aprendiz y un administrador de contenido reciben una denegacion sin cambio de rol.

**Acceptance Scenarios**:

1. **Given** un administrador de plataforma, **When** asigna el rol de administrador de contenido a una cuenta existente, **Then** el nuevo rol queda asociado a esa cuenta.
2. **Given** un administrador de plataforma, **When** retira el rol de administrador de contenido, **Then** la cuenta afectada conserva su identidad y su rol de aprendiz, y deja de tener el rol de administrador de contenido.
3. **Given** una cuenta aprendiz o un administrador de contenido, **When** intenta asignar o retirar el rol de administrador de contenido, **Then** la operacion se deniega y los roles permanecen sin cambios.
4. **Given** una cuenta autenticada, **When** modifica los datos editables de su perfil, **Then** no puede modificar ni ampliar sus propios roles.
5. **Given** un intento autenticado de asignar o retirar el rol de administrador de contenido, **When** finaliza la operacion, **Then** queda registrado su actor, accion, resultado y fecha, junto con la cuenta afectada cuando existe o una referencia no reversible del identificador solicitado cuando no existe o no tiene un formato valido.
6. **Given** un administrador de plataforma, **When** intenta asignarse o retirarse a si mismo el rol de administrador de contenido, **Then** la operacion se deniega, sus roles no cambian y se registra una auditoria denegada con actor y objetivo iguales.

### Edge Cases

- El registro se rechaza sin crear una cuenta parcial cuando falta un dato obligatorio, el correo tiene formato invalido o la contrasena no cumple la politica comunicada.
- Los espacios y diferencias de mayusculas no permiten crear duplicados del mismo correo electronico normalizado.
- Una solicitud de cierre de sesion repetida deja a la persona en estado no autenticado y no produce errores ni restaura acceso.
- Una sesion expirada se trata como no autenticada y dirige a autenticacion antes de mostrar cualquier informacion privada.
- La ruta de perfil propio no acepta identificadores de cuenta; cualquier identificador adicional se ignora y la operacion permanece limitada a la cuenta de la sesion actual, sin revelar si otra cuenta existe.
- La asignacion de rol con un identificador de cuenta inexistente o de formato invalido se rechaza sin crear identidades o permisos parciales y genera una auditoria sin cuenta objetivo asociada, con una referencia no reversible del identificador solicitado y resultado de objetivo inexistente. Solo un administrador de plataforma recibe una respuesta que distingue el objetivo no encontrado; los demas actores reciben la misma denegacion generica que ante otros intentos no autorizados.
- La asignacion o retirada del rol de administrador de contenido sobre la misma cuenta del administrador de plataforma se deniega, no cambia roles y genera una auditoria denegada con actor y objetivo iguales.
- Los intentos simultaneos de registrar el mismo correo producen como maximo una cuenta.
- Los intentos fallidos repetidos asociados a una cuenta declarada inexistente reciben la misma espera progresiva y respuesta generica que los asociados a una cuenta existente.
- Un destino posterior a la autenticacion que sea externo, malformado, inexistente o no autorizado se descarta y conduce al inicio del aprendiz.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir crear una cuenta con correo electronico, nombre visible y contrasena como datos obligatorios minimos.
- **FR-002**: El sistema DEBE exigir que cada correo electronico normalizado identifique como maximo una cuenta y DEBE impedir registros duplicados, incluso ante solicitudes simultaneas.
- **FR-003**: El sistema DEBE validar los datos obligatorios antes de crear la cuenta y DEBE evitar cuentas parciales cuando la validacion falle.
- **FR-004**: Toda cuenta creada mediante registro publico DEBE recibir el rol de aprendiz por defecto y ningun rol administrativo.
- **FR-005**: El sistema DEBE permitir que una cuenta activa inicie sesion con sus credenciales validas y DEBE rechazar credenciales invalidas sin revelar cual dato fallo.
- **FR-006**: El sistema DEBE permitir cerrar la sesion y DEBE invalidar el acceso autenticado asociado antes de confirmar el cierre.
- **FR-007**: Toda ruta declarada privada DEBE exigir una sesion valida; si no existe, DEBE dirigir a la persona a autenticacion sin mostrar contenido privado y conservar la ruta solicitada solo cuando sea un destino interno valido. Tras autenticarse, la persona DEBE volver a ese destino si continua autorizada; en cualquier otro caso, DEBE llegar al inicio del aprendiz.
- **FR-008**: Una cuenta autenticada DEBE poder consultar su propio perfil, compuesto por correo electronico, nombre visible y roles asignados.
- **FR-009**: Una cuenta autenticada DEBE poder modificar su propio nombre visible, pero NO DEBE poder modificar sus roles desde el perfil.
- **FR-010**: El sistema DEBE exponer el perfil propio sin identificadores de cuenta en la ruta, obtenerlo siempre desde la sesion actual e ignorar cualquier identificador de cuenta adicional aportado en la solicitud; una cuenta NO DEBE consultar ni modificar informacion privada de otra.
- **FR-011**: Solo un administrador de plataforma DEBE poder asignar o retirar el rol de administrador de contenido a otra cuenta existente; actor y objetivo DEBEN ser cuentas distintas. Una operacion con actor y objetivo iguales DEBE denegarse, no cambiar roles y auditarse como denegada. El rol es acumulativo con el rol de aprendiz, que DEBE conservarse tanto al asignarlo como al retirarlo, y NO DEBE conceder capacidad para administrar roles.
- **FR-012**: Un intento no autorizado de consultar datos ajenos o administrar roles, incluida una operacion de rol con actor y objetivo iguales, DEBE dejar los datos y permisos sin cambios y DEBE responder sin revelar informacion privada adicional.
- **FR-013**: La autorizacion DEBE evaluarse en el momento de cada operacion privada; conocer o aportar un identificador de cuenta adicional NO DEBE cambiar el recurso derivado de la sesion actual ni conceder acceso.
- **FR-014**: El sistema DEBE aplicar esperas progresivas ante intentos repetidos de inicio de sesion con credenciales invalidas, considerando tanto la cuenta declarada como el origen de los intentos, sin confirmar si la cuenta existe.
- **FR-015**: El sistema DEBE conservar un historial de cada intento autenticado de asignar o retirar el rol de administrador de contenido, incluyendo actor, accion, resultado y fecha. Cuando la cuenta objetivo exista, DEBE registrar esa cuenta; cuando el identificador solicitado no corresponda a una cuenta o tenga un formato invalido, DEBE dejar la cuenta objetivo sin asociar, conservar una referencia no reversible del identificador solicitado y registrar un resultado de objetivo inexistente, sin crear una identidad. Solo un administrador de plataforma DEBE recibir una respuesta que distinga el objetivo no encontrado; los demas actores DEBEN recibir una denegacion generica. Las cuentas aprendiz y los administradores de contenido NO DEBEN poder modificar este historial.

### Acceptance Criteria by Requirement

- **AC-FR-001/003**: Un registro con los tres datos validos crea una cuenta; omitir o invalidar cualquiera de ellos muestra errores comprensibles y no crea ninguna cuenta.
- **AC-FR-002**: Dos intentos de registro con variantes equivalentes o simultaneas del mismo correo producen una sola cuenta y al menos un rechazo controlado.
- **AC-FR-004**: Toda cuenta creada publicamente muestra solo el rol de aprendiz antes de cualquier accion administrativa autorizada.
- **AC-FR-005/006**: Las credenciales validas abren una sesion, las invalidas no la abren y, tras cerrar sesion, la misma sesion ya no accede a rutas privadas.
- **AC-FR-007**: Cada ruta clasificada como privada redirige a autenticacion cuando se solicita sin una sesion valida y no incluye datos privados en la respuesta; tras iniciar sesion, un destino interno valido y autorizado recupera la ruta solicitada, mientras que un destino externo, invalido o no autorizado conduce al inicio del aprendiz.
- **AC-FR-008/009**: Una persona autenticada ve su correo, nombre visible y roles, puede cambiar solo el nombre visible y no puede alterar roles desde su perfil.
- **AC-FR-010/013**: Con dos sesiones autenticadas, cada solicitud de perfil muestra y modifica solo la cuenta de su propia sesion; aportar el identificador de la otra cuenta como dato adicional no cambia el recurso derivado de la sesion ni expone o modifica informacion ajena.
- **AC-FR-011/012**: Un administrador de plataforma puede añadir el rol de administrador de contenido a otra cuenta sin retirar el de aprendiz y puede retirarlo conservando el de aprendiz; los mismos intentos de una cuenta aprendiz o un administrador de contenido se deniegan y no cambian roles. Si actor y objetivo son el mismo administrador de plataforma, la operacion se deniega, los roles no cambian y existe exactamente una auditoria denegada.
- **AC-FR-014**: Una secuencia de intentos invalidos repetidos incrementa la espera antes de aceptar el siguiente intento; la conducta observable y el mensaje son equivalentes para una cuenta existente y una inexistente.
- **AC-FR-015**: Cada intento autenticado de asignacion o retirada produce exactamente una entrada con actor, accion, resultado y fecha; usa la cuenta objetivo cuando existe o deja esa asociacion vacia, conserva una referencia no reversible y registra un resultado de objetivo inexistente cuando el identificador no corresponde a una cuenta o tiene formato invalido. En esos dos casos, solo un administrador de plataforma recibe una respuesta de objetivo no encontrado; los demas actores reciben una denegacion generica. Un intento de alterar la entrada desde una cuenta aprendiz o un administrador de contenido es denegado.

### Key Entities *(include if feature involves data)*

- **Cuenta**: Identidad de una persona; contiene un correo electronico unico, un nombre visible, credenciales protegidas, estado de actividad y sus roles.
- **Perfil**: Vista sin identificador de ruta derivada exclusivamente de la sesion actual; solo el nombre visible es editable y los identificadores de cuenta adicionales se ignoran.
- **Rol**: Conjunto acumulable de permisos asociado a una cuenta. Toda cuenta registrada conserva el rol de aprendiz y puede tener adicionalmente el rol de administrador de contenido.
- **Sesion autenticada**: Estado temporal que vincula solicitudes posteriores con una cuenta validada y que termina al cerrar sesion o expirar.
- **Administrador de plataforma**: Cuenta administrativa provisionada mediante un proceso operativo seguro y unica autoridad capaz de asignar o retirar el rol de administrador de contenido.
- **Registro de cambio de rol**: Evidencia trazable de un intento autenticado de asignar o retirar el rol de administrador de contenido; identifica actor, accion, resultado y fecha, y referencia la cuenta objetivo cuando existe o conserva una referencia no reversible del identificador solicitado cuando no corresponde a una cuenta o tiene formato invalido. No puede ser alterada por aprendices ni administradores de contenido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una prueba de aceptacion con diez participantes representativos que disponen de datos validos, al menos nueve completan sin asistencia el registro y el primer inicio de sesion en menos de 3 minutos.
- **SC-002**: El 100% de los accesos de prueba a rutas privadas sin una sesion valida terminan en autenticacion sin exponer contenido privado.
- **SC-003**: El 100% de los intentos de prueba de consultar o modificar el perfil de otra cuenta son denegados sin revelar datos privados ni producir cambios.
- **SC-004**: El 100% de las cuentas creadas mediante registro publico reciben el rol de aprendiz y ninguna recibe un rol administrativo.
- **SC-005**: El 100% de los intentos no autorizados de asignar o retirar el rol de administrador de contenido son denegados sin alterar permisos.
- **SC-006**: En la misma prueba de aceptacion de SC-001, al menos nueve de los diez participantes identifican correctamente y sin asistencia tanto el estado de sesion iniciada como el de sesion cerrada.
- **SC-007**: El 100% de las pruebas con intentos invalidos repetidos muestran una espera creciente entre intentos y respuestas que no permiten distinguir una cuenta existente de una inexistente.
- **SC-008**: El 100% de los intentos autenticados de prueba de asignar o retirar el rol de administrador de contenido, exitosos, denegados o dirigidos a identificadores inexistentes o invalidos, generan exactamente un registro completo y atribuible sin alterar los roles ante intentos no autorizados o sin objetivo valido.

## Assumptions

- Los datos minimos de registro son correo electronico, nombre visible y contrasena; no se solicitan datos demograficos ni de pago.
- El correo electronico funciona como identificador de inicio de sesion y se compara de forma normalizada.
- La politica de contrasenas se comunica antes del envio y sigue practicas de seguridad vigentes; su configuracion concreta se definira durante la planificacion.
- Las cuentas nuevas quedan activas al completar un registro valido. La verificacion de correo, recuperacion de contrasena, autenticacion externa y autenticacion multifactor quedan fuera de este alcance.
- La edicion del perfil se limita al nombre visible. Los cambios de correo y contrasena quedan fuera de este alcance.
- La lista exacta de rutas privadas se identificara durante la planificacion; todas las rutas que expongan experiencia o datos personales del aprendiz se consideran privadas.
- Los administradores de plataforma se provisionan mediante el proceso operativo seguro del proyecto; esta autoridad no se obtiene mediante el registro publico, el perfil de usuario ni el rol de administrador de contenido.
- Los objetivos de latencia y carga se definiran en una iniciativa posterior a partir de mediciones operativas; esta feature solo exige los tiempos funcionales y las esperas de seguridad expresamente incluidos en sus criterios de exito.
- No existen dependencias funcionales externas para entregar esta capacidad.

## Scope Boundaries

### In Scope

- Registro con datos minimos y rol de aprendiz por defecto.
- Inicio y cierre de sesion.
- Consulta del perfil propio y edicion del nombre visible.
- Proteccion de rutas privadas y aislamiento entre cuentas.
- Asignacion y retirada del rol de administrador de contenido exclusivamente por administradores de plataforma.

### Out of Scope

- Verificacion de correo y recuperacion o cambio de contrasena.
- Inicio de sesion con proveedores externos y autenticacion multifactor.
- Eliminacion de cuentas, exportacion de datos y preferencias avanzadas de perfil.
- Creacion, publicacion o administracion del contenido educativo.
- Objetivos especificos de latencia, carga o rendimiento operativo antes de disponer de una linea base medible.

## Dependencies

- Ninguna dependencia funcional externa.
