# Phase 0 Research: Espacio de aprendizaje

## Proyección publicada de inscripciones

**Decision**: La feature consumirá exclusivamente
`learning.services.enrollment.list_enrollments(request.user)`. Antes de implementar,
el contrato base debe mantener su orden estable y `select_related("track")`, excluir
resultados cuando la cuenta ya no esté activa y publicar un atributo entero
`module_count` por inscripción con el total actual de módulos del track.

**Rationale**: El servicio actual ya aísla por cuenta, pero no vuelve a comprobar
`Account.is_active` ni proyecta el conteo exigido por FR-003. Publicar ambos datos en
la consulta evita reglas de autorización en la vista, acceso ORM desde la plantilla
y una consulta adicional por cada track.

**Alternatives considered**:

- Usar `enrollment.track.modules.count()` en la vista o plantilla: rechazado porque
  el dato no proviene del servicio publicado y produce consultas N+1.
- Modificar `learning/services/enrollment.py` dentro de la 007: rechazado porque el
  archivo está cerrado y también pertenece al flujo de inscripción de la 008.
- Omitir el conteo: rechazado porque incumple FR-003.

## Destino de la sesión del día

**Decision**: La tarjeta revertirá `learning:session-current` con el argumento
nombrado `track_id`. La ruta debe estar publicada antes de implementar la 007; el
comportamiento de selección y renderizado de la sesión sigue siendo propiedad de la
009 y se valida de extremo a extremo después de integrar ambas features.

**Rationale**: La 004 reservó el namespace y el include `learn/session/`, pero el
módulo hoja actual tiene `urlpatterns = []`. Un nombre reversible permite que la
007 enlace mediante contrato sin editar URLs ni conocer el patrón físico.

**Alternatives considered**:

- Codificar una URL literal: rechazado porque inventaría una superficie no
  publicada y podría divergir de la 009.
- Añadir la ruta o una vista temporal desde la 007: rechazado por propiedad de
  archivos y por solaparse con la 009.
- Enlazar al detalle del catálogo: rechazado porque no conduce a la sesión del día.

## Composición de la interfaz

**Decision**: Cada entrada será un `article` que compone los parciales existentes
`ui/components/card.html` y `ui/components/button.html`; el estado sin resultados
usará `ui/components/empty_state.html`. El contenido dinámico enviado a
`card.html` debe escapar el título antes de llegar a su parámetro `content`, porque
ese parcial aplica `safe`. La cantidad numérica y la acción pertenecen al mismo
grupo accesible, sin duplicar el markup de los componentes.

**Rationale**: Esta composición respeta el inventario visual existente y evita
crear un componente fuera del alcance cerrado. El escape explícito impide que un
título administrable se interprete como HTML.

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

## Prerequisitos de implementación

Los siguientes contratos deben existir antes de `/speckit-implement`:

1. `list_enrollments(account)` no devuelve inscripciones si la cuenta persistida no
   está activa.
2. Cada resultado de `list_enrollments(account)` expone `module_count` sin consultas
   adicionales por track.
3. `reverse("learning:session-current", kwargs={"track_id": track.id})` resuelve.

No quedan `NEEDS CLARIFICATION`; los faltantes están identificados como dependencias
externas y no como trabajo autorizado para la 007.
