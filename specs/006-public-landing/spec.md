# Feature Specification: Portada pública de KronoLearn

**Feature Branch**: `006-public-landing`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Como visitante que llega por primera vez a KronoLearn, quiero ver una página de inicio pública en la raíz del sitio que me explique brevemente qué es la plataforma y me ofrezca crear una cuenta o iniciar sesión, para decidir si quiero registrarme."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conocer KronoLearn y elegir cómo entrar (Priority: P1)

Como visitante, quiero encontrar una portada pública que explique brevemente qué es KronoLearn y me permita crear una cuenta o iniciar sesión para decidir cómo comenzar.

**Why this priority**: La raíz del sitio es el primer contacto con la plataforma. Sin una explicación breve y caminos claros de acceso, un visitante no puede comprender la propuesta ni continuar hacia el producto.

**Independent Test**: Una persona sin sesión abre la raíz del sitio, recibe la portada sin autenticarse, identifica qué ofrece KronoLearn y puede seguir enlaces distintos para crear una cuenta o iniciar sesión.

**Acceptance Scenarios**:

1. **Given** una persona sin sesión iniciada, **When** abre `/`, **Then** recibe una respuesta `200` que muestra la portada pública sin redirigirla al inicio de sesión.
2. **Given** un visitante en la portada, **When** revisa su contenido, **Then** encuentra una explicación breve de KronoLearn y de su propósito de aprendizaje.
3. **Given** un visitante en la portada, **When** decide comenzar, **Then** encuentra enlaces operables y claramente diferenciados para crear una cuenta y para iniciar sesión.

---

### User Story 2 - Continuar al espacio de aprendizaje (Priority: P2)

Como usuario autenticado, quiero ir desde la portada a mi espacio de aprendizaje para continuar mi recorrido sin buscar otra entrada.

**Why this priority**: La portada también debe servir como punto de paso para quienes ya tienen una cuenta, sin sustituir ni duplicar el espacio de aprendizaje.

**Independent Test**: Una cuenta activa con sesión iniciada abre la portada, activa el acceso al espacio de aprendizaje y llega a `/learn/` en una sola acción.

**Acceptance Scenarios**:

1. **Given** una cuenta activa con sesión iniciada en la portada, **When** elige continuar aprendiendo, **Then** llega a `/learn/`.
2. **Given** una cuenta activa que inició sesión correctamente, **When** termina el proceso de acceso, **Then** continúa aterrizando en `/learn/`.

---

### User Story 3 - Conservar la protección del aprendizaje (Priority: P3)

Como responsable de la plataforma, quiero que abrir la portada no debilite la protección del espacio de aprendizaje para que solo las cuentas activas puedan acceder a él.

**Why this priority**: Hacer pública la raíz del sitio no debe convertir en público el contenido reservado ni cambiar el contrato de acceso ya vigente.

**Independent Test**: Se intenta abrir `/learn/` sin una cuenta activa y se confirma que el acceso sigue rechazado o dirigido al proceso de autenticación; con una cuenta activa, el acceso sigue permitido.

**Acceptance Scenarios**:

1. **Given** una persona sin sesión iniciada, **When** intenta abrir `/learn/`, **Then** no recibe el espacio de aprendizaje y se le dirige al inicio de sesión conservando el destino solicitado.
2. **Given** una cuenta que no está activa, **When** intenta abrir `/learn/`, **Then** no recibe el espacio de aprendizaje.
3. **Given** una cuenta activa con sesión iniciada, **When** abre `/learn/`, **Then** recibe el espacio de aprendizaje.

### Edge Cases

- Si una persona autenticada abre directamente `/`, la portada permanece disponible y ofrece el acceso a `/learn/`; no la redirige automáticamente ni pierde las opciones públicas.
- Si una persona sin cuenta intenta seguir el acceso al espacio de aprendizaje, la protección vigente de `/learn/` decide el acceso y la portada no revela contenido reservado.
- Los enlaces de registro e inicio de sesión deben conservar destinos válidos aunque la persona vuelva a la portada mediante navegación del navegador.
- Si el contenido estático de la portada no puede cargar recursos decorativos, el texto y los enlaces principales deben seguir siendo comprensibles y operables.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ofrecer una portada pública exactamente en `/` y responder con estado `200` cuando una persona sin sesión iniciada la consulta, sin redirigirla.
- **FR-002**: La portada DEBE explicar de forma breve y comprensible qué es KronoLearn y qué valor ofrece a una persona que evalúa registrarse.
- **FR-003**: La portada DEBE incluir enlaces operables y claramente diferenciados para crear una cuenta y para iniciar sesión mediante los flujos existentes.
- **FR-004**: La portada DEBE ofrecer a una persona autenticada un acceso operable a `/learn/` para continuar con su aprendizaje.
- **FR-005**: La ruta raíz pública DEBE conservar el identificador estable `ui:index`; al resolver `/`, el resultado DEBE ser `ui:index`.
- **FR-006**: La incorporación de la portada NO DEBE cambiar la exigencia de una cuenta activa para consultar `/learn/`.
- **FR-007**: La incorporación de la portada NO DEBE cambiar el destino posterior a un inicio de sesión exitoso, que DEBE seguir siendo `/learn/`.
- **FR-008**: Todo el contenido propio de la portada DEBE ser estático y NO DEBE depender de contenido administrable ni de consultas a datos persistidos.
- **FR-009**: La portada NO DEBE incluir blog, precios, testimonios, formulario de contacto ni selección de idioma.
- **FR-010**: Esta especificación DEBE observar los principios aplicables 4, 6, 9 y 11 de la constitución vigente sobre seguridad por defecto, verificación obligatoria, entrega incremental e interfaz accesible, sin redefinir sus reglas globales.

### Acceptance Criteria by Requirement

- **AC-FR-001-005**: Una comprobación de la raíz confirma una respuesta `200` para visitantes, una explicación breve de KronoLearn, enlaces separados y operables a registro e inicio de sesión, acceso visible a `/learn/` para cuentas autenticadas y el identificador de ruta `ui:index` al resolver `/`.
- **AC-FR-006-007**: Las comprobaciones de regresión confirman que una persona sin cuenta activa no accede a `/learn/`, una cuenta activa sí accede y todo inicio de sesión exitoso sigue aterrizando en `/learn/`.
- **AC-FR-008-009**: La portada puede presentarse sin consultar contenido persistido y una inspección de su contenido confirma que no incorpora blog, precios, testimonios, formulario de contacto ni selección de idioma.
- **AC-FR-010**: La revisión de conformidad identifica evidencia automatizada del acceso público a la portada, la protección conservada de `/learn/`, la navegación completa mediante teclado y el significado comprensible de enlaces y acciones sin depender solo del color.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las visitas de comprobación realizadas sin sesión iniciada puede abrir la raíz del sitio y ver la portada sin autenticarse.
- **SC-002**: En una validación con cinco personas que no conocen KronoLearn, al menos cuatro pueden explicar en sus propias palabras el propósito de la plataforma e identificar las dos opciones de acceso en 30 segundos o menos.
- **SC-003**: El 100% de las personas autenticadas de la prueba puede llegar desde la portada al espacio de aprendizaje en una sola acción.
- **SC-004**: El 100% de las comprobaciones de acceso confirma que las personas sin cuenta activa siguen sin poder consultar el espacio de aprendizaje.
- **SC-005**: El 100% de los inicios de sesión exitosos de la prueba continúa llevando al espacio de aprendizaje.
- **SC-006**: El 100% de las acciones principales de la portada puede localizarse y activarse usando únicamente el teclado.

## Assumptions

- Los flujos de creación de cuenta e inicio de sesión ya existen y mantienen sus destinos actuales; esta feature únicamente ofrece enlaces hacia ellos.
- El espacio de aprendizaje ya existe en `/learn/`, admite cuentas activas y conserva su protección vigente.
- Una cuenta autenticada también puede consultar la portada pública; la diferencia relevante es que dispone de una acción para continuar al espacio de aprendizaje.
- La explicación de KronoLearn es texto editorial estático y breve, suficiente para comunicar el propósito sin incorporar nuevas secciones comerciales o administrables.
- Los términos "respuesta correcta" y "recibe 200" describen que la raíz entrega satisfactoriamente la portada solicitada.

## Scope Boundaries

### In Scope

- Portada pública en la raíz del sitio.
- Explicación breve y estática de KronoLearn.
- Enlaces a los flujos existentes de registro e inicio de sesión.
- Acceso desde la portada al espacio de aprendizaje para cuentas autenticadas.
- Verificación de que la protección y el destino posterior al inicio de sesión permanecen sin cambios.
- Identificación estable de la raíz como `ui:index`.

### Out of Scope

- Blog.
- Precios.
- Testimonios.
- Formulario de contacto.
- Selección de idioma.
- Contenido administrable desde datos persistidos.
- Cambios en registro, autenticación o en el espacio de aprendizaje.

## Dependencies

- Los flujos existentes de registro e inicio de sesión deben permanecer disponibles para recibir visitantes desde la portada.
- El espacio de aprendizaje y su control vigente de cuenta activa deben permanecer disponibles en `/learn/`.
- El destino configurado para un inicio de sesión exitoso debe continuar apuntando a `/learn/`.
- El enrutamiento raíz existente debe admitir la incorporación de la portada sin modificar la configuración principal del sitio.

## Constraints

- `kronolearn/urls.py` no puede modificarse como parte de esta feature.
- La portada no puede introducir consultas a datos persistidos ni contenido administrable.
- La feature debe limitarse a abrir la raíz pública y enlazar capacidades existentes; no debe redefinir sus reglas de negocio o acceso.
