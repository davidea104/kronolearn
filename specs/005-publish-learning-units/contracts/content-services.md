# Contract: Servicios de contenido

**Module**: `catalog.services.content`  
**Scope**: Interfaces Python estables implementadas por feature 005

## Tipos publicos

```python
@dataclass(frozen=True)
class ContentLoadOutcome:
    changed: bool
    track_count: int
    module_count: int
    content_item_count: int
    items_created: int
    versions_created: int


class ContentRevisionConflict(Exception): ...


class ContentLoadConflict(Exception): ...
```

Las excepciones no contienen correo ni UUID de cuentas en su representacion textual.

## Crear borrador

```python
def create_content_draft(
    module: Module,
    actor,
    payload: Mapping[str, object],
) -> ContentItem: ...
```

Payload aceptado:

```python
{"expected_revision": 1}
```

Precondiciones:

- `module` y `actor` representan filas persistidas; el servicio usa `accounts.services.queries.resolve_content_admin` para volver a resolver y bloquear al actor.
- `expected_revision` es un entero positivo y coincide con la revision bloqueada del modulo.
- Las posiciones existentes del modulo son consecutivas desde 1.
- El actor persistido esta activo y pertenece al rol `content_admin` al ejecutar.

Efectos en exito:

- Crea un `ContentItem` `DRAFT` en la siguiente posicion consecutiva.
- Incrementa una vez `module.revision`.
- Devuelve la unidad creada.
- La unidad empieza con `revision=1` y `published_version=0`.

Errores:

| Condicion | Resultado |
| --- | --- |
| Actor inexistente, inactivo o no autorizado | `PermissionDenied` generico |
| Payload o secuencia invalida | `ValidationError` sin escrituras |
| Revision esperada obsoleta | `ContentRevisionConflict` sin escrituras |
| Conflicto de integridad concurrente no reconciliable | `ContentRevisionConflict` sin escrituras parciales |

## Publicar unidad

```python
def publish_content_item(
    content_item: ContentItem,
    actor,
    payload: Mapping[str, object],
) -> ContentVersion: ...
```

Payload aceptado:

```python
{
    "expected_revision": 1,
    "title": "...",
    "learning_objective": "...",
    "lesson_text": "...",
    "case_prompt": "...",
    "source": "KronoLearn curriculum 005/principal/01 | ...",
    "reviewed_on": date(2026, 8, 22),
    "choices": (
        {
            "position": 1,
            "text": "...",
            "rating": "OPTIMAL",
            "consequence": "...",
            "explanation": "...",
        },
        # Dos o tres opciones adicionales con posiciones consecutivas.
    ),
    "lab": None,
}
```

`lab` puede ser `None` o este mapping:

```python
{
    "objective": "...",
    "initial_prompt": "...",
    "expected_artifact": "...",
    "verification_checklist": ("...",),
}
```

Precondiciones:

- La revision esperada es positiva y coincide con la unidad bloqueada.
- El actor persistido esta activo y tiene `content_admin`.
- Todos los textos y metadatos satisfacen los limites del modelo.
- Hay tres o cuatro opciones con posiciones `1..N`, textos distintos y al menos una `OPTIMAL`.
- Si existe laboratorio, todos sus campos son validos.

Efectos en exito:

- Crea una `ContentVersion` con el siguiente numero.
- Crea todas sus opciones y, cuando procede, un laboratorio dentro de la misma transaccion.
- Deriva `author` del actor bloqueado, fija `editorial_status=PUBLISHED` y deja que el modelo asigne `published_at`; el payload no puede elegir esos valores.
- Cambia la unidad a `PUBLISHED`, actualiza `published_version` e incrementa `revision` una vez.
- Devuelve la nueva version; las versiones anteriores permanecen identicas.

Errores:

| Condicion | Resultado |
| --- | --- |
| Actor inexistente, inactivo o no autorizado | `PermissionDenied` generico |
| Payload, metadatos, opciones o laboratorio invalidos | `ValidationError` por campo, sin version parcial |
| Revision esperada obsoleta | `ContentRevisionConflict` sin escrituras |
| Conflicto de integridad concurrente no reconciliable | `ContentRevisionConflict` sin escrituras parciales |

## Reconciliar conjunto de despliegue

```python
def load_learning_content(
    actor_ref: str,
    definitions: tuple[TrackDefinition, ...],
) -> ContentLoadOutcome: ...
```

Precondiciones:

- `actor_ref` procede de configuracion privada del servidor e identifica una cuenta persistida, activa y con `content_admin`.
- `definitions` pasa la validacion completa 2/2/10, orden 7/3, opciones 3/4 y laboratorios 7/0 antes de la primera escritura.
- Los objetos existentes en posiciones administradas tienen linaje compatible y no existen unidades adicionales en los dos modulos objetivo.

Efectos:

- Ejecuta toda la carga en una sola transaccion.
- Resuelve y bloquea al actor mediante `accounts.services.queries.resolve_content_admin`, bloquea `CatalogState` y despues entidades en orden determinista.
- Crea o reconcilia tracks y modulos mediante sus servicios de dominio existentes.
- Crea unidades mediante `create_content_draft` y publica mediante `publish_content_item`.
- Omite toda escritura para instantaneas que ya coinciden.
- Devuelve siempre conteos finales 2/2/10 en exito.

Errores:

| Condicion | Resultado |
| --- | --- |
| Actor inexistente, inactivo o no autorizado | `PermissionDenied`; rollback total |
| Definicion invalida | `ValidationError`; cero escrituras |
| Contenido extra, posicion rota o linaje incompatible | `ContentLoadConflict`; rollback total |
| Resultado `INVALID`, `NOT_FOUND`, `DENIED` o `CONFLICT` de un servicio subordinado | Excepcion de dominio equivalente; rollback total |

## Idempotencia y concurrencia

- Una ejecucion convergida devuelve `changed=False`, `items_created=0` y `versions_created=0`.
- Dos ejecuciones simultaneas validas terminan con exito. La primera que obtiene el lock puede escribir; la segunda relee el estado convergido y no crea duplicados.
- La igualdad de una version compara todos los campos editoriales, incluido `editorial_status=PUBLISHED`, opciones ordenadas y laboratorio. Ignora IDs, `published_at` y el autor ya persistido.
- Ninguna funcion modifica o elimina snapshots publicados.