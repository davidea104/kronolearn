# Phase 0 Research: Espacio de aprendizaje

## Proyección publicada de inscripciones

**Decision**: La feature consume exclusivamente
`learning.services.enrollment.list_enrollments(request.user)`. Su tarea fundacional
mantiene el orden estable y `select_related("track")`, rechaza la operación cuando
la cuenta persistida ya no está activa y publica un atributo entero `module_count`
por inscripción con el total actual de módulos del track.

**Rationale**: El servicio actual ya aísla por cuenta, pero no vuelve a comprobar
`Account.is_active` ni proyecta el conteo exigido por FR-003. Publicar ambos datos en
la consulta evita reglas de autorización en la vista, acceso ORM desde la plantilla
y una consulta adicional por cada track.

**Alternatives considered**:

- Usar `enrollment.track.modules.count()` en la vista o plantilla: rechazado porque
  el dato no proviene del servicio publicado y produce consultas N+1.
- Implementar `enroll()` junto con la proyección: rechazado porque el flujo de
  inscripción pertenece a la 008 y no es necesario para esta pantalla de lectura.
- Omitir el conteo: rechazado porque incumple FR-003.

## Destino de la sesión del día

**Decision**: La tarjeta revierte `learning:session-current` con el argumento
nombrado `track_id`. La tarea fundacional publica una vista temporal protegida con
respuesta `200`; la selección y el renderizado real de la sesión siguen siendo
propiedad de la 009, que reemplazará el cuerpo conservando nombre y argumento.

**Rationale**: La 004 reservó el namespace y el include `learn/session/`, pero el
módulo hoja actual tiene `urlpatterns = []`. Un nombre reversible permite que la
007 enlace mediante contrato sin editar URLs ni conocer el patrón físico.

**Alternatives considered**:

- Codificar una URL literal: rechazado porque inventaría una superficie no
  publicada y podría divergir de la 009.
- Implementar ya la selección de sesión: rechazado porque se solaparía con la 009.
- Enlazar al detalle del catálogo: rechazado porque no conduce a la sesión del día.

## Composición de la interfaz

**Decision**: Cada entrada usa `ui/components/card.html`, que conserva `content` y
añade una API estructurada compatible para título, metadatos y acción. Esa rama
escapa el título automáticamente e incluye `ui/components/button.html`; el estado
sin resultados usa `ui/components/empty_state.html`.

**Rationale**: Esta composición respeta el inventario visual existente y evita
construir HTML en Python. La rama estructurada impide que un título administrable
pase por el parámetro histórico `content|safe`.

**Alternatives considered**:

- Replicar a mano las clases de tarjeta o botón: rechazado por la regla de uso de
  componentes.
- Construir HTML de la tarjeta en Python: rechazado porque mezcla presentación con
  la vista y amplía la superficie de escape.
- Pasar el título sin escapar a `card.content`: rechazado por riesgo de XSS.

## Flujo de la vista y plantilla canónica

**Decision**: `learner_home` conservará `@active_account_required`, llamará al
servicio una vez y renderizará `ui/learner_home.html` con `enrollments`. La nueva
plantilla vivirá en `templates/ui/learner_home.html` y se eliminará
`ui/templates/ui/learner_home.html` en el mismo cambio.

**Rationale**: No se modifica la ruta, el decorador ni settings. El traslado deja
una sola fuente de plantilla y la evaluación del QuerySet permite distinguir entre
listado y estado vacío sin una consulta de existencia separada.

**Alternatives considered**:

- Conservar las dos plantillas: rechazado porque la precedencia de loaders ocultaría
  una copia y permitiría divergencia.
- Consultar modelos desde `ui.views`: rechazado por la frontera modular.

## Estrategia de pruebas

**Decision**: Ampliar `tests/ui/test_learner_home.py` con Django `TestCase` y las
factories existentes para cubrir listado propio, conteo cero y múltiple, estado
vacío, aislamiento entre cuentas, escape de títulos, redirección anónima con
`next=/learn/`, rechazo de cuenta inactiva y destino posterior al login. La suite
rápida usa settings de test; CI vuelve a ejecutar `tests.ui` en PostgreSQL.

**Rationale**: Son pruebas de integración de presentación y autorización, sin
escrituras concurrentes ni migraciones. La matriz existente ya ejecuta el mismo
paquete en ambos motores.

**Alternatives considered**:

- Mocks del servicio: rechazados para los escenarios de aislamiento y proyección,
  que deben comprobar la consulta publicada real.
- Pruebas de navegador como única evidencia: rechazadas porque los criterios
  principales son verificables con respuestas HTML y resolución de URLs.

## Contratos fundacionales implementados

T002 implementa y prueba los siguientes contratos antes de las historias:

1. `list_enrollments(account)` no devuelve inscripciones si la cuenta persistida no
   está activa.
2. Cada resultado de `list_enrollments(account)` expone `module_count` sin consultas
   adicionales por track.
3. `reverse("learning:session-current", kwargs={"track_id": track.id})` resuelve.

No quedan `NEEDS CLARIFICATION` ni dependencias externas para ejecutar las historias.
