# Contract: Comando de carga de contenido

**Command**: `python manage.py load_learning_content`  
**Owner**: `catalog`  
**Purpose**: Reconciliar el contenido inicial durante un despliegue

## Invocation

```text
python manage.py load_learning_content
```

### Server configuration

| Variable | Requerida | Regla |
| --- | --- | --- |
| `CONTENT_AUTHOR_ACCOUNT_ID` | Si | Referencia privada a una cuenta preexistente que sera resuelta y autorizada por el servicio de `accounts`. |

El comando no acepta identidad, rutas de datos, contenido parcial, fechas dinamicas, `--dry-run` ni opciones propias de `seed_demo` como argumentos.

## Data source

El comando solicita a `catalog.content_data` que cargue `learning_units.json` y reciba definiciones inmutables ya validadas. No agrega, transforma ni elige textos, opciones, posiciones, fuentes, fechas o laboratorios durante la ejecucion.

## Behavior

1. Django obtiene `settings.CONTENT_AUTHOR_ACCOUNT_ID`; una configuracion ausente se rechaza sin iniciar la carga.
2. El comando pasa la referencia privada y la definicion completa a `catalog.services.content.load_learning_content`.
3. El servicio ejecuta autorizacion, validacion, bloqueo, reconciliacion y persistencia.
4. El comando presenta el resultado sin consultar ni escribir modelos directamente.

El comando no invoca, importa ni modifica `ui.management.commands.seed_demo`. Ambas operaciones pueden ejecutarse en secuencia sobre una base desechable: la carga reconoce las dos unidades legacy compatibles y completa el conjunto sin duplicarlas.

## Exit contract

| Caso | Codigo | Salida observable |
| --- | --- | --- |
| Primera carga valida | 0 | Mensaje de exito con conteos 2 tracks, 2 modulos y 10 unidades, mas cantidades creadas. |
| Estado ya convergido | 0 | Mensaje de exito que indica cero unidades y cero versiones creadas. |
| Dos cargas simultaneas validas | 0 para ambas | Ambas observan el mismo resultado final; como maximo una informa escrituras. |
| Configuracion ausente, cuenta inexistente, inactiva o no autorizada | Distinto de 0 | `CommandError` generico, sin confirmar existencia ni mostrar identificadores. |
| Definicion invalida | Distinto de 0 | `CommandError` que identifica la categoria de validacion, sin contenido sensible. |
| Unidad extra o posicion incompatible | Distinto de 0 | `CommandError` de conflicto o colision; no hay cambios parciales. |
| Error inesperado | Distinto de 0 | La excepcion se propaga para conservar diagnostico y provocar rollback. |

## Output privacy

La salida puede contener conteos, estado `created/updated/unchanged` y titulos publicos de tracks. No contiene correo, UUID de cuenta, credenciales, tokens ni datos de conexion. El comando no registra `CONTENT_AUTHOR_ACCOUNT_ID` ni acepta un argumento equivalente.

## Deployment ordering

```text
migrate --noinput
load_learning_content
start web process
```

La cuenta autora, su rol y la variable privada deben existir antes del segundo paso. Railway configura migracion y carga en Pre-Deploy; la operacion no pertenece a la demostracion ni al arranque de cada proceso web.