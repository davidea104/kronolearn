# UI Contract: Learner Home

## Endpoint

- **Nombre**: `ui:learner-home`
- **Método**: `GET`
- **Ruta pública**: `/learn/`
- **Representación**: documento HTML server-rendered
- **Vista propietaria**: `ui.views.learner_home`

No se añaden métodos, parámetros de consulta, cuerpos de solicitud ni variantes
HTMX.

## Control de acceso

| Estado | Resultado |
| --- | --- |
| Anónimo | Redirección a `accounts:login` con `next=/learn/`. |
| Cuenta autenticada e inactiva | No recibe el documento ni datos de inscripciones. |
| Cuenta autenticada y activa | Respuesta `200` con listado propio o estado vacío. |

La identidad se toma únicamente de `request.user`. El endpoint no acepta un
identificador de cuenta por URL, formulario, header ni query string.

## Contrato de consulta

La vista invoca una vez:

```text
learning.services.enrollment.list_enrollments(request.user)
```

El resultado conserva el orden del servicio y publica por fila:

- `track.id`;
- `track.title`;
- `module_count`.

La vista no importa modelos de `learning` ni `catalog`, no cuenta relaciones y no
aplica filtros adicionales. Los prerequisitos exactos están en
[../research.md](../research.md#prerequisitos-de-implementación).

## Contexto de plantilla

| Clave | Tipo | Descripción |
| --- | --- | --- |
| `enrollments` | QuerySet iterable | Inscripciones propias en orden estable, con track y conteo publicados. |

No se requiere otro dato de dominio.

## Estado con inscripciones

Por cada elemento se renderiza exactamente una entrada que contiene:

1. título escapado del track;
2. cantidad total de módulos, incluido cero;
3. una acción creada con `ui/components/button.html` cuyo `href` es
   `learning:session-current` revertida con `track_id=track.id`.

La superficie visual se compone con `ui/components/card.html`. El valor pasado a
`card.content` no puede contener texto administrable sin escapar.

## Estado vacío

Cuando `enrollments` no contiene filas, se renderiza
`ui/components/empty_state.html` con:

- un titular que indique que aún no hay tracks inscritos;
- un mensaje que oriente el siguiente paso;
- una acción a `catalog:track-list`.

No se renderizan contenedores de track vacíos.

## Datos excluidos

La respuesta no contiene:

- inscripciones ni títulos exclusivos de otra cuenta;
- correo, identificador interno ni estado de otra cuenta;
- porcentaje de progreso, puntos, racha o recomendaciones;
- consultas o cálculos de módulos ejecutados desde la plantilla.

## Accesibilidad y seguridad

- Las acciones son enlaces operables por teclado con foco visible y área mínima
  heredados del componente de botón.
- El título es texto escapado incluso si contiene caracteres de markup.
- Ningún estado depende solo del color.
- El orden del documento permite identificar título, conteo y acción de cada track.

## Integraciones conservadas

- `active_account_required` permanece aplicado a la vista.
- Un login válido sin `next` continúa redirigiendo a `ui:learner-home`.
- No cambian `ui/urls.py`, settings ni la composición raíz de URLs.
