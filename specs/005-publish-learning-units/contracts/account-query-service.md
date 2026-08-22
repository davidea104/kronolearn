# Contract: Consulta autorizada de cuentas

**Module**: `accounts.services.queries`  
**Consumer**: `catalog.services.content`  
**Scope**: Resolver identidad server-side sin exponer lecturas directas del modelo `Account`

## Resolver administrador de contenido

```python
def resolve_content_admin(
    actor_ref: str,
    *,
    for_update: bool = False,
): ...
```

Precondiciones:

- `actor_ref` procede de una sesion del servidor o de configuracion privada para un proceso no interactivo.
- El llamador usa `for_update=True` dentro de una transaccion atomica cuando la operacion escribe datos.
- La referencia no se incluye en logs, errores ni resultados de dominio.

Efectos:

- Convierte y busca la referencia dentro del modulo `accounts`.
- Cuando `for_update=True`, bloquea la fila antes de evaluar autorizacion.
- Comprueba que la cuenta exista, este activa y pertenezca al rol `content_admin`.
- Devuelve la cuenta persistida autorizada para usarla como actor y autor de la operacion.

Errores:

| Condicion | Resultado |
| --- | --- |
| Referencia ausente o mal formada | `PermissionDenied` generico |
| Cuenta inexistente | `PermissionDenied` generico |
| Cuenta inactiva | `PermissionDenied` generico |
| Cuenta sin `content_admin` | `PermissionDenied` generico |
| `for_update=True` fuera de una transaccion | Error de transaccion sin degradar a lectura desbloqueada |

Todos los rechazos de identidad son observacionalmente equivalentes. Ningun mensaje confirma la existencia de una cuenta ni contiene correo, UUID, digest reutilizable u otro identificador interno.

## Frontera modular

- Solo `accounts.services.queries` importa y consulta `accounts.models.Account` para esta operacion.
- `catalog.services.content` importa `resolve_content_admin`, no `Account`.
- El comando de despliegue no consulta cuentas; entrega al servicio de catalogo la referencia obtenida de `settings.CONTENT_AUTHOR_ACCOUNT_ID`.
- Los servicios de catalogo vuelven a resolver y autorizar el actor en el momento de cada mutacion, incluso cuando reciben un objeto actor desde una vista.

## Concurrencia

La carga completa usa `resolve_content_admin(actor_ref, for_update=True)` como primer lock de su transaccion. Las demas mutaciones conservan el mismo orden: actor, estado global de catalogo cuando corresponda, agregado propietario y entidades hijas. La consulta nunca crea, activa ni asigna roles a cuentas.
