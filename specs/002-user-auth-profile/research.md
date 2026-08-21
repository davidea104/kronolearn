# Phase 0 Research: Autenticacion y perfil

**Date**: 2026-08-20
**Spec**: [spec.md](spec.md)

## Custom Account Model

**Decision**: Crear `accounts.Account` en `accounts/migrations/0001_initial.py`, heredando de `AbstractUser`, con `username = None`, UUID como clave primaria, `email` canonico y unico como `USERNAME_FIELD`, y `display_name` obligatorio.

**Rationale**: La especificacion usa correo como identificador y el proyecto no tiene migraciones. Django recomienda fijar `AUTH_USER_MODEL` antes de la primera migracion y crear el modelo intercambiable en la migracion inicial. `AbstractUser` conserva hashing, sesiones, `is_active`, permisos y compatibilidad con admin con menos codigo propio que `AbstractBaseUser`.

**Alternatives considered**:

- Usuario Django por defecto mas perfil `OneToOne`: rechazado porque mantiene un `username` que el dominio no usa y dificulta cambiar el identificador despues de migrar.
- `AbstractBaseUser` desde cero: rechazado porque duplica comportamiento de permisos y admin sin aportar valor a este alcance.

## Email Canonicalization and Concurrency

**Decision**: Normalizar el correo con `strip()` y `casefold()` antes de validar o persistir, mantener `unique=True` y capturar `IntegrityError` alrededor del bloque atomico de registro.

**Rationale**: La especificacion considera equivalentes espacios y mayusculas. La forma canonica hace que variantes concurrentes compitan por la misma restriccion PostgreSQL y evita depender solo de una consulta previa vulnerable a carreras.

**Alternatives considered**:

- Comparacion case-insensitive solo en formularios: rechazada porque no protege escrituras concurrentes ni otros puntos de entrada.
- Extension PostgreSQL `citext`: rechazada para evitar una extension adicional cuando el almacenamiento canonico satisface el dominio.

## Password Policy

**Decision**: Reutilizar los validadores Django existentes y configurar longitud minima de 15 caracteres, maximo de formulario de 128, aceptando espacios y Unicode sin reglas obligatorias de composicion.

**Rationale**: MFA esta fuera de alcance. OWASP considera debiles las contrasenas inferiores a 15 caracteres cuando no hay MFA y recomienda longitud, bloqueo de contrasenas comunes y compatibilidad con gestores de contrasenas antes que reglas de simbolos.

**Alternatives considered**:

- Mantener el minimo Django predeterminado de 8: rechazado por el riesgo superior en una autenticacion sin MFA.
- Exigir mayusculas, digitos y simbolos: rechazado porque penaliza usabilidad y no mejora tanto como longitud y blocklist.

## Role Representation

**Decision**: Usar `django.contrib.auth.models.Group` con grupos canonicos `learner` y `content_admin`; toda cuenta publica recibe `learner`, el rol de contenido se agrega o retira sin eliminarlo, y `is_superuser` identifica al administrador de plataforma.

**Rationale**: Django permite multiples grupos por cuenta y resuelve permisos acumulativos de forma nativa. `createsuperuser` ofrece el proceso operativo seguro solicitado para la autoridad de plataforma.

**Alternatives considered**:

- Campos booleanos por rol: rechazados porque escalan mal y duplican el sistema de permisos.
- Tabla de roles propia: rechazada porque replicaria grupos y permisos de Django.
- Permitir que `content_admin` conceda su rol: rechazado por la aclaracion que reserva esta accion al administrador de plataforma.

## Registration Transaction

**Decision**: `register_account()` crea la cuenta y agrega el grupo `learner` dentro de `transaction.atomic()`; un fallo deja cero cuentas parciales.

**Rationale**: Satisface FR-002/003/004 y hace que identidad y rol inicial formen una sola unidad consistente.

**Alternatives considered**:

- Signal `post_save`: rechazado porque oculta el flujo, complica errores y puede dejar una cuenta sin rol si el receptor falla fuera del caso esperado.
- Agregar el grupo desde la vista: rechazado por duplicar una regla de dominio en la capa HTTP.

## Login Throttling

**Decision**: Persistir `LoginThrottleBucket` en PostgreSQL con scopes `ACCOUNT` y `ORIGIN`, claves HMAC no reversibles, contador, ultimo fallo y `blocked_until`. Aplicar espera exponencial `min(2^(n-1), 60)` segundos y reiniciar buckets inactivos despues de 15 minutos; la demora efectiva es el maximo de ambos scopes.

**Rationale**: El backend Django no incluye proteccion de fuerza bruta. PostgreSQL funciona entre procesos Gunicorn sin introducir Redis. Combinar cuenta y origen reduce brute force distribuido y password spraying; el cap evita bloqueo permanente y la pseudonimizacion evita almacenar correo o IP en claro.

**Alternatives considered**:

- Memoria local o `LocMemCache`: rechazada porque cada proceso tendria contadores distintos y se perderian al reiniciar.
- Bloqueo fijo de cuenta: rechazado por la aclaracion y por facilitar denegacion de servicio contra terceros.
- Paquete externo de throttling: rechazado porque la regla progresiva dual y la restriccion de infraestructura pueden resolverse con el stack existente.

## Authentication Flow and Generic Errors

**Decision**: Subclasificar `AuthenticationForm` y `LoginView`, mantener una unica respuesta generica para credenciales invalidas, cuentas inexistentes, inactivas o temporalmente demoradas, y usar una comprobacion de password no utilizable para equilibrar el camino de cuenta inexistente.

**Rationale**: Django integra sesiones y rotacion de identificador en `LoginView`; OWASP exige evitar discrepancias de mensaje, estado y coste que permitan enumerar cuentas.

**Alternatives considered**:

- Backend de autenticacion completamente nuevo: rechazado porque el correo ya puede ser `USERNAME_FIELD` y `ModelBackend` satisface credenciales y permisos.
- Mensajes diferenciados: rechazados por FR-005/014.

## Safe Post-Login Redirects

**Decision**: Validar `next` con same-origin HTTPS y una allowlist de nombres de ruta retornables; resolver el destino y revalidar autorizacion. Cualquier valor externo, malformado, inexistente o no autorizado usa `ui:learner-home`.

**Rationale**: Django ya limita hosts en `LoginView`, pero la aclaracion tambien exige autorizacion del destino. Una allowlist explicita evita open redirects y saltos hacia operaciones administrativas.

**Alternatives considered**:

- Aceptar cualquier URL relativa: rechazada porque una ruta interna tambien puede requerir privilegios mayores.
- Redirigir siempre al inicio: rechazada porque pierde el contexto de la ruta privada solicitada.

## Profile Ownership

**Decision**: Exponer solo `/accounts/profile/`, obtener la cuenta desde `request.user`, aceptar un formulario con `display_name` como unico campo editable e ignorar cualquier identificador de cuenta adicional enviado como query string o campo no declarado. Verificar el aislamiento con dos sesiones autenticadas independientes.

**Rationale**: Eliminar un identificador de cuenta de la ruta evita por construccion el acceso directo inseguro a perfiles ajenos. Un `ModelForm` con lista explicita de campos descarta identificadores y campos privilegiados sin hacer consultas arbitrarias, mientras que la prueba con dos clientes demuestra que la sesion, y no datos aportados por el navegador, controla la propiedad.

**Alternatives considered**:

- `/accounts/<uuid>/profile/`: rechazada porque agrega una superficie IDOR innecesaria para un perfil exclusivamente propio.
- Modelo `Profile` separado: rechazado porque el unico dato adicional pertenece a identidad y produciria un join sin beneficio.
- Rechazar identificadores adicionales con un error distinguible: rechazado porque no aporta proteccion adicional y puede revelar detalles de la superficie interna; se ignoran como cualquier campo no declarado.

## Audited Role Changes

**Decision**: Las rutas de assign/revoke capturan la referencia solicitada con `<str:target_ref>` y delegan todo intento autenticado en `change_content_role(actor, target_ref, action)`. El servicio intenta interpretar la referencia como UUID, resuelve el objetivo cuando es valido, deniega actor igual a objetivo, verifica `is_superuser` en cada llamada y crea exactamente un `RoleChangeLog`. Para un objetivo existente guarda la relacion; para un UUID inexistente o una referencia de formato invalido deja `target` nulo, guarda un HMAC-SHA256 no reversible y usa `TARGET_NOT_FOUND`. Las denegaciones sobre objetivos existentes, incluido el autoobjetivo, usan `DENIED` y nunca modifican grupos.

**Rationale**: Centraliza parsing, resolucion, autorizacion, atomicidad y trazabilidad, por lo que las vistas y el enrutador no pueden omitir auditorias en ramas de error. Para un UUID valido se firma su representacion canonica; para una referencia invalida se firma el segmento decodificado recibido, siempre con un salt de proposito exclusivo y sin registrarlo en claro. Esto permite correlacionar intentos equivalentes sin crear identidades ficticias. El rechazo explicito de actor igual a objetivo impide que incluso un administrador de plataforma use esta interfaz para alterar su propio rol.

**Alternatives considered**:

- Editar grupos directamente desde Django admin: rechazado porque permitiria omitir auditoria y la regla de autoridad.
- Signals `m2m_changed`: rechazados porque no capturan con claridad actor, motivo ni intentos denegados.
- Exigir una relacion `target` para toda auditoria: rechazado porque perderia intentos contra cuentas inexistentes o forzaria identidades artificiales.
- Guardar el UUID solicitado en claro: rechazado porque conserva un identificador innecesario cuando el objetivo no existe.
- Permitir autoasignacion a superusuarios: rechazado por la regla explicita de separacion entre actor y objetivo.
- Usar `<uuid:target_id>` en la ruta: rechazado porque Django devolveria `404` antes de autenticar, autorizar y auditar una referencia de formato invalido.
- Crear un converter que escriba auditorias: rechazado porque el enrutador no debe ejecutar reglas de dominio ni dispone del actor autenticado.

## Representative Acceptance Protocol

**Decision**: Validar SC-001 y SC-006 en una unica sesion de aceptacion con diez participantes representativos. Cada participante recibe datos validos y, sin asistencia, debe registrarse, completar el primer login, cerrar sesion e identificar verbalmente o en el registro de observacion los estados de sesion iniciada y cerrada. El tiempo se mide desde que se presenta el formulario de registro hasta que aparece el primer inicio autenticado; al menos nueve deben completar esa parte en menos de tres minutos y cumplir tambien la identificacion de ambos estados.

**Rationale**: Un denominador fijo convierte el umbral del 90% en una prueba reproducible y combina los dos criterios sin duplicar participantes. La ausencia de ayuda comprueba que etiquetas, errores, navegacion y estado de sesion son comprensibles por si mismos. La evidencia agregada evita incorporar credenciales o datos personales a los artefactos de revision.

**Alternatives considered**:

- Inferir usabilidad solo desde tests automatizados: rechazado porque no prueba que una persona reconozca los estados ni complete el flujo sin asistencia.
- Medir registro, login y logout en muestras separadas: rechazado porque impediria relacionar SC-001 y SC-006 sobre los mismos diez participantes.
- Conservar grabaciones o credenciales de participantes: rechazado por minimizacion de datos; bastan tiempos, resultados y observaciones agregados.

## Operational Performance Baseline

**Decision**: No fijar en esta feature umbrales de latencia, percentiles, concurrencia volumetrica ni carga. Mantener como criterios verificables el limite humano de registro y primer login, las esperas progresivas de seguridad y la consistencia transaccional bajo carreras dirigidas. Definir objetivos operativos en una iniciativa posterior a partir de mediciones del despliegue representativo.

**Rationale**: No existe una linea base, volumen esperado ni perfil de carga que sustente un umbral. Convertir una cifra arbitraria en gate produciria una promesa no trazable a la especificacion y mezclaria el tiempo funcional humano con la latencia del sistema.

**Alternatives considered**:

- Mantener un objetivo general inferior a un segundo: rechazado porque la aclaracion lo excluye y no define percentil, carga ni entorno reproducible.
- Agregar pruebas de carga a CI: rechazado hasta establecer una linea base y un escenario operativo representativo.
- Eliminar las pruebas concurrentes: rechazado porque verifican correccion e idempotencia, no capacidad o latencia.

## Audit Protection and Observability

**Decision**: Hacer `RoleChangeLog` de solo append en servicios y de solo lectura en admin, sin endpoints de cambio/borrado. Derivar las referencias de objetivos inexistentes con un proposito/salt HMAC separado de los buckets de throttling. Emitir eventos estructurados de login, throttling y cambios de rol mediante `logging`, usando UUID y digests, nunca password, cookie, token ni correo/IP en claro.

**Rationale**: La base de datos ofrece trazabilidad consultable dentro del monolito; los logs de aplicacion permiten detectar ataques sin agregar un servicio externo y respetan minimizacion de datos.

**Alternatives considered**:

- Solo logs de texto: rechazados porque no garantizan el registro de negocio requerido por FR-015.
- Sistema externo de observabilidad: rechazado por las restricciones de infraestructura de la linea base.

## Web Interface

**Decision**: Usar formularios Django y HTML renderizado en servidor, con POST para registro, login, logout, perfil y cambios de rol; CSRF obligatorio, redireccion POST/Redirect/GET y mejora HTMX opcional en la tabla administrativa sin depender de JavaScript.

**Rationale**: Encaja con el monolito, conserva accesibilidad y funciona sin frontend separado. Logout por POST evita que navegacion o prefetch cierren sesiones.

**Alternatives considered**:

- API JSON y SPA: rechazadas por alcance y constitucion.
- Logout por GET: rechazado por semantica y proteccion CSRF.

## Validation Toolchain

**Decision**: Seguir CI: `ruff check .`, `ruff format --check .`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `python manage.py test` y prueba directa de PostgreSQL.

**Rationale**: Son las puertas ya operativas; las pruebas de concurrencia y bloqueo usan `TransactionTestCase`, y el resto usa `TestCase`/cliente Django.

**Alternatives considered**:

- Introducir pytest: rechazado porque el repositorio no lo usa y no aporta capacidad necesaria.

## Research Resolution

Todos los detalles necesarios para Phase 1 estan resueltos. No quedan marcadores `NEEDS CLARIFICATION`.
