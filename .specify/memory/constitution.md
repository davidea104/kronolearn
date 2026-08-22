<!--
Sync Impact Report

- Version change: 1.2.0 -> 1.3.0
- Modified principles:
  - 1 "Desarrollo guiado por especificaciones" (global rules are referenced, not duplicated)
  - 2 "Diseño orientado al dominio" -> "Autoridad del dominio"
  - 5 "Idempotencia transaccional" -> "Idempotencia e integridad"
  - 6 "Pruebas de reglas críticas" -> "Verificación obligatoria"
  - 11 "Sistema visual coherente" -> "Frontend server-rendered y accesible"
- Modified sections: Governance (constitutional requirements must not be copied into feature specs)
- Added sections:
  - principle 12 "Autorización en profundidad"
  - principle 13 "Privacidad por minimización"
  - principle 14 "Comunicación entre módulos"
  - principle 15 "Tiempo determinista"
  - principle 16 "Propiedad de archivos y migraciones"
- Removed sections: none
- Follow-up TODOs: none

-->

# KronoLearn Constitution

## Core Principles

### 1. Desarrollo guiado por especificaciones

Ninguna funcionalidad puede implementarse antes de contar con su especificación, las aclaraciones necesarias,
un plan técnico, la lista de tareas y criterios de aceptación verificables. Los criterios de aceptación DEBEN ser
automáticamente verificables cuando sea posible (tests, validaciones, scripts de revisión).

Las especificaciones DEBEN referenciar esta constitución y NO DEBEN repetir sus reglas globales. Solo pueden
añadir requisitos específicos de la feature que no estén ya gobernados aquí.

### 2. Autoridad del dominio

Las reglas de negocio DEBEN vivir en servicios de dominio claramente definidos. Las vistas, formularios, plantillas
y fragmentos HTMX NO DEBEN calcular puntuación, rachas, progreso, intentos, versionado, selección de contenido,
clasificación ni autorización; solo pueden recopilar entrada, invocar servicios y presentar resultados. Todo valor
que el cliente pueda manipular DEBE derivarse de nuevo en el servidor desde datos autoritativos.

Esta separación mantiene una única implementación verificable de cada regla e impide que el cliente o una capa de
presentación alteren decisiones del dominio.

### 3. Contenido administrado como datos

Los tracks, módulos, microlecciones, casos, opciones, fuentes y laboratorios DEBEN poder configurarse y publicarse
sin modificar el código fuente de la aplicación. La publicación y el versionado DEBEN poder realizarse desde
interfaces administrativas o pipelines de datos controlados.

### 4. Seguridad por defecto

La autenticación, autorización, validación de propiedad de los recursos, protección CSRF, validación del lado del
servidor, administración de secretos y protección de datos privados SON obligatorias. El sistema NUNCA debe confiar
en datos de autorización, puntuación, progreso o valoración provenientes del navegador.

### 5. Idempotencia e integridad

Toda operación que otorgue puntos, registre progreso o produzca auditoría DEBE ser idempotente. La garantía DEBE
estar respaldada por una restricción única en la base de datos; una comprobación previa en Python NO constituye una
garantía de idempotencia. Los envíos repetidos NUNCA deben duplicar puntos competitivos, progreso, intentos puntuables,
eventos de puntuación ni registros de auditoría.

Toda operación compuesta, incluidos el registro del intento, la actualización del progreso, el cálculo de la racha y
la creación de sus eventos, DEBE ocurrir en una sola transacción. Estas garantías evitan duplicados y estados parciales
incluso ante concurrencia, reintentos o fallos intermedios.

### 6. Verificación obligatoria

Son obligatorias las pruebas automatizadas para:

- cálculo de puntos;
- bonificación y ruptura de rachas;
- identificación del primer intento;
- idempotencia;
- actualización del progreso;
- publicación y versionado de contenido;
- permisos de aprendiz y administrador;
- selección de la siguiente sesión;
- ordenamiento y desempate de la liga semanal.

Las reglas críticas de dominio, la autorización y la idempotencia DEBEN probarse siempre. La concurrencia, las
migraciones y la auditoría DEBEN verificarse contra una instancia real de PostgreSQL y NUNCA contra SQLite. Estas
pruebas DEBEN ejecutarse en CI y bloquear merges si fallan. Ninguna tarea puede declararse completa sin ejecutar las
pruebas que la verifican.

### 7. Main siempre desplegable

Todo cambio DEBE llegar a `main` mediante Pull Request y solo puede integrarse después de superar correctamente
los controles de integración continua. La rama `main` DEBE permanecer siempre desplegable en Railway. No se permiten
commits directos a `main`.

### 8. Monolito modular

KronoLearn DEBE implementarse como un monolito modular en Django con los siguientes módulos:

- `accounts`;
- `catalog`;
- `learning`;
- `gamification`;
- `analytics`;
- `ui`.

Durante la línea base NO se deben introducir microservicios, Redis, workers, cron, colas de tareas ni un frontend
desplegado por separado.

### 9. Entrega simple e incremental

El equipo DEBE priorizar el flujo funcional completo del aprendiz sobre el pulido visual y las funcionalidades
opcionales. El flujo prioritario es:

inicio de sesión → exploración → inscripción → sesión diaria → decisión → retroalimentación → puntos → progreso.

Si existe un retraso, se DEBE reducir el contenido precargado o el pulido visual antes de eliminar controles de
seguridad, autorización, idempotencia o pruebas de dominio.

### 10. Contenido trazable y versionado

Cada versión publicada de contenido DEBE conservar como mínimo:

- autor;
- fuente;
- número de versión;
- fecha de revisión;
- estado editorial.

Las versiones publicadas DEBEN ser inmutables y los intentos históricos DEBEN conservar la versión exacta presentada
al aprendiz.

### 11. Frontend server-rendered y accesible

La interfaz DEBE renderizarse en el servidor. HTMX DEBE usarse para solicitudes y reemplazo parcial, Alpine.js para
estado local de la interfaz y Tailwind CSS para estilos. Ningún estado de dominio puede vivir en el cliente. Las
interfaces DEBEN ser operables mediante teclado y su significado NUNCA puede transmitirse solo mediante color.

Todo componente visual nuevo DEBE cumplir `.github/instructions/design.instructions.md`, fuente de verdad del sistema
visual de KronoLearn. La implementación DEBE respetar sus tokens, tipografía, accesibilidad, estados visuales, reglas
de foco, áreas mínimas de toque, movimiento reducido y restricciones de sombras, colores y estructura. Los
componentes DEBEN mantenerse como parciales reutilizables bajo `templates/ui/components/`, sin lógica de negocio ni
acceso a la base de datos. Toda revisión de un componente nuevo DEBE comprobar explícitamente su conformidad con dicha
guía.

La regla existe para evitar divergencias visuales y garantizar que los componentes nuevos sean consistentes,
accesibles y reutilizables sin convertir el navegador en una segunda autoridad del dominio.

### 12. Autorización en profundidad

La autorización DEBE comprobarse en el servicio de dominio, además de cualquier control inicial de la vista, y DEBE
evaluarse en el momento de la operación. La identidad DEBE obtenerse de la sesión del servidor; ningún identificador
de cuenta puede viajar en formularios ni en URLs. Las vistas NO DEBEN decidir permisos por sí mismas: el servicio
autoritativo debe volver a comprobarlos con el estado vigente.

Ante falta de permiso o recurso inexistente, la respuesta DEBE ser genérica y NO DEBE permitir distinguir un caso del
otro. Esto evita decisiones obsoletas, suplantación de identidad y filtraciones sobre la existencia de recursos.

### 13. Privacidad por minimización

Ningún log, registro de auditoría, agregado ni respuesta puede contener contraseñas, correos electrónicos, direcciones
IP, tokens ni identificadores internos de cuenta. Las referencias inválidas DEBEN registrarse mediante un digest HMAC
y NUNCA mediante el valor recibido. Los paneles agregados DEBEN suprimir el detalle cuando se calculen sobre menos del
mínimo configurable de personas.

Estas restricciones reducen la exposición de datos sensibles tanto en las rutas de éxito como en las de error y
evitan que los agregados permitan identificar a una persona.

### 14. Comunicación entre módulos

Un módulo NO DEBE importar servicios de otro para reaccionar a un hecho del dominio; DEBE suscribirse a la señal
correspondiente. Las dependencias de lectura entre módulos DEBEN pasar por servicios de consulta publicados y NUNCA
por los modelos de otra app.

Esta frontera conserva el monolito modular, evita acoplamiento circular y permite que cada app controle sus modelos y
contratos de escritura.

### 15. Tiempo determinista

El día calendario y la semana DEBEN calcularse con la zona horaria fija configurada por el proyecto y NUNCA con la
zona horaria del navegador. Los límites de medianoche y de cambio de semana DEBEN estar cubiertos por pruebas.

Una referencia temporal única garantiza resultados reproducibles para progreso, rachas, ligas y auditoría.

### 16. Propiedad de archivos y migraciones

Cada feature DEBE declarar en su plan la lista cerrada de archivos que puede modificar y NO DEBE salir de ella. Solo
una feature por app de Django puede añadir migraciones al mismo tiempo. La fusión de migraciones divergentes DEBE
contar con coordinación explícita entre sus responsables.

Estas restricciones hacen revisable el alcance de cada feature y evitan historiales de migración incompatibles.

## Restricciones tecnológicas

Las siguientes tecnologías son obligatorias y forman parte del contrato técnico del proyecto:

- Django
- PostgreSQL
- HTMX
- Alpine.js
- Tailwind CSS
- Gunicorn
- WhiteNoise
- GitHub Actions
- Railway

Durante la línea base, no se introducirán otras infraestructuras externas salvo las listadas anteriormente.

## Desarrollo y flujo de trabajo

### Revisión y puertas de calidad

- Todos los cambios DEBEN presentarse como Pull Requests y pasar la suite de CI.
- Los PRs que alteren comportamiento público DEBEN incluir una entrada de changelog y la guía de migración cuando
  corresponda.
- Se requiere al menos una aprobación de un mantenedor o revisor designado antes del merge.

### Versionado y releases

- Se usa versionado semántico: MAJOR.MINOR.PATCH.
- Los cambios incompatibles DEBEN provocar un MAJOR bump y acompañarse de guía de migración.
- Cada release DEBE incluir notas y changelog.

## Governance

- Esta constitución prevalece sobre cualquier práctica, guía o artefacto del proyecto que entre en conflicto con ella.
- Toda enmienda DEBE presentarse en un Pull Request dedicado que actualice el Sync Impact Report, explique el motivo
  y el impacto, incluya un plan de migración cuando corresponda y cuente con la aprobación de un mantenedor.
- La versión de la constitución sigue MAJOR.MINOR.PATCH: MAJOR para eliminaciones o redefiniciones incompatibles de
  principios; MINOR para principios, secciones o reglas materialmente ampliadas; PATCH para aclaraciones sin cambio
  semántico.
- Cada revisión de especificaciones, aclaraciones, planes, tareas, implementaciones y Pull Requests DEBE comprobar
  el cumplimiento constitucional. Las desviaciones no críticas DEBEN documentarse y justificarse en un issue o PR
  enlazado antes de aprobarse.
- Las especificaciones individuales DEBEN referenciar los principios globales aplicables y NO DEBEN copiarlos ni
  reformularlos. Las enmiendas a reglas globales solo pueden realizarse en esta constitución.
- Las reglas críticas de seguridad, autorización, pruebas e idempotencia NO pueden omitirse ni exceptuarse para
  cumplir una fecha de entrega.
- Toda enmienda DEBE actualizar la versión y `Last Amended`; `Ratified` conserva la fecha de adopción original.

**Version**: 1.3.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-21
