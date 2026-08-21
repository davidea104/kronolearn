# Implementation Plan: Autenticacion y perfil

<!-- markdownlint-disable MD060 -->

**Branch**: `002-user-auth-profile` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-user-auth-profile/spec.md`

## Summary

Implementar registro por correo, inicio y cierre de sesion, perfil propio, proteccion de rutas privadas y gestion auditada del rol de administrador de contenido dentro del modulo `accounts`. La solucion usa el sistema de autenticacion y sesiones de Django con un modelo de cuenta personalizado creado en la primera migracion, grupos acumulativos para roles, servicios de dominio transaccionales para registro, throttling y cambios de rol, y vistas HTML renderizadas en el servidor con proteccion CSRF. Cada intento autenticado de cambiar el rol se audita, incluidos identificadores inexistentes o con formato invalido y operaciones del administrador sobre si mismo.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, psycopg 3.3.4, HTMX, Alpine.js y Tailwind CSS ya previstos por la linea base; no se agregan paquetes Python ni infraestructura externa

**Storage**: PostgreSQL para cuentas, sesiones, grupos/permisos, buckets de throttling y auditoria de roles

**Testing**: `django.test.TestCase` y `TransactionTestCase` ejecutados con `python manage.py test`; Ruff 0.16.3 para lint y formato; pruebas sobre PostgreSQL

**Target Platform**: Aplicacion web Linux desplegada en Railway mediante Gunicorn y WhiteNoise

**Project Type**: Monolito web modular Django con HTML renderizado en servidor

**Performance Goals**: Al menos nueve de diez participantes representativos completan sin asistencia el registro y primer inicio de sesion en menos de 3 minutos e identifican correctamente los estados de sesion iniciada y cerrada; cambios de rol y auditoria permanecen consistentes bajo solicitudes concurrentes; los objetivos operativos de latencia y carga se difieren hasta disponer de una linea base medible

**Constraints**: HTTPS y cookies seguras en produccion; CSRF y validacion en servidor; mensajes de autenticacion genericos; redirecciones solo a destinos internos permitidos; contrasenas de al menos 15 caracteres sin reglas de composicion; sin Redis, workers, cron, colas, microservicios ni frontend separado

**Scale/Scope**: Cinco flujos HTML (registro, login, logout, perfil y gestion de roles), tres roles observables (aprendiz, administrador de contenido y administrador de plataforma) y tres entidades propias persistidas; la correccion concurrente prima sobre una cifra de volumen no definida por la especificacion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Status | Evidence |
|-----------|--------|----------|
| 1. Desarrollo guiado por especificaciones | PASS | `spec.md` esta validada y contiene once aclaraciones, 15 requisitos y criterios verificables. |
| 2. Diseno orientado al dominio | PASS | Registro, throttling y cambios de rol se concentran en `accounts/services/`; las vistas solo adaptan HTTP. |
| 3. Contenido administrado como datos | N/A | La feature no crea ni publica contenido educativo. |
| 4. Seguridad por defecto | PASS | El diseno exige CSRF, perfil derivado solo de la sesion, permisos en servidor, rechazo de autoedicion de roles, respuestas genericas, redirects internos y referencias sensibles pseudonimizadas. |
| 5. Idempotencia transaccional | PASS | Unicidad de correo y cambios de rol se protegen con restricciones y transacciones; cada intento autenticado de rol genera una sola auditoria incluso sin objetivo resuelto. |
| 6. Pruebas de reglas criticas | PASS | El plan incluye pruebas automatizadas de permisos, autoobjetivo, aislamiento entre sesiones, sesiones, concurrencia, throttling y auditoria con objetivos existentes, inexistentes y de formato invalido. |
| 7. Main siempre desplegable | PASS | Se reutilizan los comandos de CI existentes y no se omite ninguna puerta. |
| 8. Monolito modular | PASS | Todo el dominio queda en `accounts`, con presentacion compartida en `ui`; no se agrega infraestructura. |
| 9. Entrega simple e incremental | PASS | Se priorizan registro/login, luego perfil y finalmente gestion de roles. |
| 10. Contenido trazable y versionado | N/A | No se modifica contenido educativo. |

**Gate result**: PASS. No hay violaciones que requieran Complexity Tracking.

### Post-Design Gate

El modelo de datos, los contratos HTML y la guia de validacion conservan los limites anteriores: no duplican reglas en vistas o templates, no introducen servicios externos y hacen verificables propiedad por sesion, permisos, rechazo de autoobjetivo, throttling, atomicidad, auditoria de identificadores inexistentes o invalidos y el protocolo de aceptacion de diez participantes. No se introduce una puerta de latencia o carga sin linea base. **Result: PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/002-user-auth-profile/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── web-auth.md
└── tasks.md                 # Creado posteriormente por /speckit-tasks
```

### Source Code (repository root)

```text
accounts/
├── admin.py
├── forms.py
├── managers.py
├── models.py
├── security.py
├── urls.py
├── views.py
├── services/
│   ├── __init__.py
│   ├── registration.py
│   ├── roles.py
│   └── throttling.py
└── migrations/
    ├── __init__.py
    ├── 0001_initial.py
    └── 0002_seed_roles.py

ui/
├── urls.py
├── views.py
└── templates/
    ├── base.html
    ├── accounts/
    │   ├── login.html
    │   ├── profile.html
    │   ├── register.html
    │   └── role_management.html
    └── ui/
        └── learner_home.html

kronolearn/
├── urls.py
└── settings/
    ├── base.py
    ├── development.py
    └── production.py

tests/
├── accounts/
│   ├── test_models.py
│   ├── test_profile.py
│   ├── test_registration.py
│   ├── test_roles.py
│   ├── test_sessions.py
│   └── test_throttling.py
└── ui/
    └── test_learner_home.py
```

**Structure Decision**: Mantener el monolito modular existente. `accounts` es propietario de identidad, permisos, throttling y auditoria; `ui` aporta el layout y el inicio minimo del aprendiz. No se crea API separada ni capa frontend desplegable.

## Design Decisions

1. `accounts.Account` hereda de `AbstractUser`, elimina `username`, usa UUID como clave primaria y correo canonico unico como `USERNAME_FIELD`.
2. `AUTH_USER_MODEL` se configura antes de la primera migracion del proyecto; todas las relaciones usan `settings.AUTH_USER_MODEL`.
3. Los grupos `learner` y `content_admin` representan roles acumulativos. `is_superuser` representa al administrador de plataforma provisionado con `createsuperuser`.
4. El registro crea cuenta y membresia `learner` dentro de una transaccion. La restriccion unica y el manejo de `IntegrityError` cubren registros concurrentes.
5. `LoginThrottleBucket` persiste contadores por cuenta declarada y origen pseudonimizados con HMAC. La espera es exponencial de 1 segundo hasta un maximo de 60 segundos dentro de una ventana de 15 minutos.
6. El login reutiliza `AuthenticationForm`/`LoginView` con formulario y validacion de throttling personalizados. Los errores mantienen cuerpo, estado y coste comparables para cuentas existentes e inexistentes.
7. `accounts.security` centraliza `canonicalize_account_email()` y `resolve_safe_next()`. Los redirects `next` se aceptan solo si son same-origin y su nombre de URL aparece en un mapa inmutable de predicados de autorizacion; el fallback es `ui:learner-home`.
8. El perfil no recibe identificador de cuenta: siempre lee y actualiza `request.user`, limita el formulario a `display_name` e ignora identificadores y campos adicionales. Dos clientes autenticados independientes prueban que cada solicitud permanece ligada a su propia sesion.
9. Las rutas de assign/revoke capturan un unico segmento no vacio con `<str:target_ref>` para que los identificadores de formato invalido alcancen la vista autenticada. `change_content_role(actor, target_ref, action)` es el unico punto de entrada: intenta interpretar el UUID, resuelve y bloquea la cuenta cuando procede, verifica `is_superuser` y exige actor distinto del objetivo. Un UUID inexistente o un valor invalido produce `TARGET_NOT_FOUND`, `target` nulo y un HMAC no reversible de la referencia solicitada; un autoobjetivo o actor sin autoridad sobre un objetivo existente produce `DENIED`. La capa HTTP devuelve `404` solo al administrador de plataforma para `TARGET_NOT_FOUND` y una denegacion `403` generica a los demas actores.
10. Cada invocacion autenticada crea exactamente un `RoleChangeLog`. Para un objetivo existente, el bloqueo de la cuenta, la mutacion opcional del grupo y la auditoria comparten una transaccion; para denegaciones y objetivos inexistentes, la auditoria se confirma antes de devolver la respuesta de error y no hay mutacion.
11. La interfaz de gestion de roles esta reservada a administradores de plataforma. La auditoria se expone solo como lectura en Django admin y no ofrece rutas de edicion o borrado.
12. La aceptacion de usabilidad usa diez participantes representativos sin asistencia. Al menos nueve deben completar registro y primer login en menos de tres minutos e identificar correctamente los estados de sesion iniciada y cerrada; se conserva solo evidencia agregada sin credenciales ni identificadores personales.
13. Esta feature no fija umbrales de latencia, percentiles ni carga. Las esperas de throttling y el limite funcional humano siguen siendo verificables, mientras que las metas operativas se definiran en una iniciativa posterior basada en mediciones.

## Complexity Tracking

No hay violaciones constitucionales que justificar.
