# Quickstart Validation: Administracion de tracks y modulos

**Purpose**: Validar la feature de extremo a extremo despues de implementarla.
**Spec**: [spec.md](spec.md)
**Contract**: [contracts/web.md](contracts/web.md)
**Data model**: [data-model.md](data-model.md)

## Prerrequisitos

- Python 3.14 y dependencias bloqueadas de `requirements.txt`.
- PostgreSQL 16 local o compatible, dedicado a desarrollo y pruebas de concurrencia.
- PowerShell abierto en la raiz del repositorio.
- Una cuenta superusuario operativa, dos cuentas con rol `content_admin` y una cuenta con rol `learner`.
- Solo datos y credenciales locales; no usar produccion ni una base compartida.

## Entorno

Definir para el proceso actual de PowerShell:

```powershell
$env:DJANGO_SETTINGS_MODULE = "kronolearn.settings.development"
$env:SECRET_KEY = "local-only-secret-key-change-me"
$env:DEBUG = "True"
$env:DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/kronolearn"
```

Crear el entorno e instalar el lock si hace falta:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

## Esquema y cuentas

Aplicar las comprobaciones sobre una base local vacia o una copia desechable:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --noinput
```

Esperado:

- Django no informa problemas de configuracion.
- No quedan cambios de modelo sin migracion.
- La migracion de `catalog` crea el singleton `CatalogState`, constraints e indices.
- Los roles `learner` y `content_admin` siguen disponibles.

Crear el administrador de plataforma si el entorno no lo tiene:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Desde `/accounts/platform/roles/`, asignar `content_admin` a dos cuentas locales. Mantener una tercera cuenta solo con `learner`.

## Verificacion automatizada

Ejecutar primero la suite funcional de catalogo con la configuracion rapida:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.catalog --settings=kronolearn.settings.test -v 2
```

Ejecutar despues las pruebas de transacciones y bloqueos contra PostgreSQL. La variable `DATABASE_URL` debe apuntar a una instancia donde Django pueda crear y eliminar su base de pruebas:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.catalog.test_ordering_services --settings=kronolearn.settings.development -v 2
```

No aceptar SQLite como evidencia de `select_for_update()`, orden concurrente o secuencias de publicacion concurrentes. Las pruebas PostgreSQL deben usar `TransactionTestCase` y conexiones independientes.

Ejecutar todos los gates del repositorio:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m unittest tests.db.test_db_connection -v
```

Esperado: cada comando termina con codigo `0`; las pruebas cubren permisos, CSRF, unicidad normalizada, constraints, orden, conflictos, versionado, inmutabilidad, auditoria y consultas activas.

## Validacion manual end-to-end

Iniciar el servidor:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abrir `http://127.0.0.1:8000/accounts/login/`. Usar ventanas privadas separadas para los dos administradores y el aprendiz.

### Escenario 1: Crear la estructura inactiva

1. Iniciar sesion como primer administrador de contenido y abrir `/catalog/manage/tracks/`.
2. Crear los tracks `Fundamentos` y `Practica aplicada` con descripcion y audiencia.
3. Abrir los modulos de `Fundamentos` y crear `Introduccion`, `Conceptos clave` y `Cierre`.
4. Confirmar que cada elemento nace inactivo y aparece al final de su secuencia.
5. Intentar crear ` fundamentos ` como otro track y ` INTRODUCCION ` como otro modulo del mismo track.
6. Crear `Introduccion` dentro de `Practica aplicada`.

Esperado: las variantes equivalentes se rechazan sin filas parciales; el mismo titulo de modulo en otro track se acepta; posiciones y revisiones iniciales son coherentes.

### Escenario 2: Validacion y campos protegidos

1. Intentar crear y editar con campos vacios, solo espacios y valores que excedan cada limite comunicado.
2. Enviar una posicion, estado, revision, autor o `title_key` adicional mediante las herramientas del navegador.
3. Intentar editar un modulo agregando un `track` distinto al payload.
4. Al publicar, probar como fuente una URL y una referencia documental interna con espacios exteriores; rechazar solo espacios y mas de 500 caracteres.

Esperado: los datos invalidos muestran errores sin cambios; los campos extra no conceden control; el modulo conserva padre, posicion y estado; ambas formas de fuente validas se aceptan normalizadas sin imponer formato URL.

### Escenario 3: Publicar modulo y track

1. Intentar activar `Fundamentos` sin modulos activos.
2. Activar `Introduccion` con fuente, fecha de revision no futura y estado `APPROVED`.
3. Activar `Fundamentos` con metadata equivalente.
4. Repetir ambas activaciones sin cambios.
5. Revisar versiones desde Django admin con el superusuario.

Esperado: el primer intento de track se rechaza; cada primera activacion crea version 1 con actor servidor; repetir la accion es idempotente y no crea version 2.

### Escenario 4: Editar contenido activo e inactivo

1. Editar titulo u objetivo del modulo activo sin completar metadata editorial.
2. Repetir con metadata completa.
3. Editar el track activo con metadata completa.
4. Editar un elemento inactivo sin metadata.
5. Comparar los snapshots antes y despues desde la vista de solo lectura.

Esperado: omitir metadata conserva datos y version; las ediciones activas aceptadas crean la siguiente version por elemento; editar inactivo no publica; snapshots anteriores permanecen identicos.

### Escenario 5: Reordenar tracks y modulos

1. Crear suficientes tracks y modulos para tener al menos tres en cada secuencia.
2. Mover un elemento de ultima a primera posicion, luego al centro y despues al final.
3. Repetir con HTML normal y con HTMX habilitado.
4. Solicitar posiciones `0`, negativas, no numericas y mayores que el total.
5. Recargar y verificar el orden persistido.

Esperado: cada orden valido queda consecutivo desde 1 sin duplicados ni huecos; HTML usa `303`, HTMX reemplaza solo las filas; cada error conserva exactamente la secuencia previa e informa el rango.

### Escenario 6: Conflicto entre administradores

1. Abrir la misma edicion en las dos sesiones administrativas antes de guardar.
2. Guardar un cambio valido desde la primera y despues guardar desde la segunda sin recargar.
3. Cargar el mismo control de estado en ambas sesiones, cambiarlo desde la primera y solicitar desde la segunda ese mismo estado con la revision ya obsoleta.
4. Repetir el ejercicio con un reordenamiento basado en la misma revision de orden.
5. Recargar en la segunda sesion y reintentar deliberadamente.

Esperado: el primer cambio gana; toda solicitud obsoleta recibe `409`, incluso cuando pide el estado ya vigente, no sobrescribe datos ni crea version, pide recargar y puede completarse solo con la revision vigente. Las pruebas automatizadas PostgreSQL son la evidencia autoritativa de simultaneidad real.

### Escenario 7: Catalogo del aprendiz

1. Iniciar sesion como aprendiz y abrir `/learn/catalog/`.
2. Confirmar que ve `Fundamentos`, pero no tracks inactivos, en el orden administrativo.
3. Abrir el track y confirmar que solo aparecen sus modulos activos en orden.
4. Abrir directamente un modulo activo mediante su URL.
5. Probar UUIDs de track/modulo inactivos, inexistentes, malformados y una combinacion padre-hijo incorrecta.

Esperado: el contenido activo retorna `200`; todos los casos no visibles retornan el mismo `404` generico sin estado, metadata, revision, version ni auditoria.

### Escenario 8: Desactivacion e invariante activa

1. Con `Fundamentos` activo y un solo modulo activo, intentar desactivar ese modulo.
2. Activar otro modulo y volver a desactivar el primero.
3. Desactivar el track y comprobar inmediatamente el catalogo del aprendiz.
4. Anotar la version publicada, cambiar estados de modulos mientras el track esta inactivo y reactivar el track con metadata nueva.
5. Repetir la activacion con la revision vigente y volver a consultar las versiones.

Esperado: no se permite dejar vacio un track activo; al existir reemplazo, el modulo se oculta sin reordenar; desactivar el track oculta toda la ruta sin cambiar estados de modulos; al reactivarlo solo reaparecen los que siguen activos y se crea exactamente la siguiente version; repetir la activacion vigente no crea otra.

### Escenario 9: Autorizacion y CSRF

1. Como aprendiz, abrir cada ruta administrativa GET y enviar POST de crear, editar, activar, desactivar y reordenar usando referencias existentes e inexistentes.
2. Repetir un POST sin CSRF y otro con metodo GET sobre una ruta de mutacion.
3. Cerrar sesion e intentar una ruta privada con `next` interno y luego con destino externo o administrativo no autorizado.

Esperado: GET y POST no autorizados retornan `403` generico sin datos; ningun intento muta contenido. CSRF invalido retorna `403`, GET de mutacion `405`, usuario anonimo vuelve a login y destinos inseguros caen en `/learn/`.

### Escenario 10: Auditoria e inmutabilidad

1. Desde Django admin, revisar el log de cambios como superusuario.
2. Correlacionar cada POST administrativo autenticado que supero CSRF y alcanzo el servicio con exactamente una fila.
3. Confirmar actor, accion, tipo/ID de elemento cuando se resolvio, resultado, `changed` y fecha.
4. Verificar resultados `SUCCESS`, `INVALID`, `CONFLICT`, `NOT_FOUND` y `DENIED`.
5. Repetir una referencia inexistente o malformada y comprobar que se conserva un digest correlacionable, no el texto solicitado; confirmar que el UUID resuelto y el digest nunca coexisten.
6. Intentar editar o eliminar auditoria y snapshots desde admin y mediante URL directa.

Esperado: cada comando autenticado que alcanza el servicio tiene un unico resultado; los POST anonimos o rechazados por CSRF no crean auditoria. Los rechazos de dominio no aparecen como cambios, las referencias crudas fallidas se sustituyen por HMAC-SHA256 no reversible y auditoria/versiones son de solo lectura.

## Protocolo manual de aceptacion del equipo

1. Convocar tres integrantes del equipo y preparar para cada uno una cuenta administrativa local autorizada y desechable.
2. Preparar catalogos desechables equivalentes para medir el flujo individual sin interferencias.
3. Entregar solo el objetivo: crear un track con tres modulos, ordenarlos y dejar la ruta disponible para aprendices.
4. Medir desde la primera vista administrativa hasta la confirmacion del track activo.
5. Pedir que cada participante identifique el estado y orden que observa el aprendiz, sin asistencia.
6. Preparar un catalogo compartido y hacer que dos participantes carguen la misma revision. El primero envia un cambio valido y el segundo envia despues un cambio distinto con la revision obsoleta.
7. Pedir al tercer participante que verifique que se conservo el primer cambio, que el segundo recibio conflicto sin sobrescritura y que, tras recargar, puede reintentar sobre la revision vigente.
8. Registrar solo conteos agregados, duraciones y resultado de la ronda de colision; no conservar credenciales, payloads ni identificadores de participantes.

Esperado: 3 de 3 terminan en menos de 5 minutos, los mismos 3 identifican estado y orden, y la ronda de colision conserva el primer cambio, rechaza el obsoleto y permite el reintento, cumpliendo SC-001 y SC-006.

## Comprobacion de rendimiento

Ejecutar el harness reproducible sobre PostgreSQL con:

```powershell
$env:RUN_CATALOG_BENCHMARK = "1"
.\.venv\Scripts\python.exe manage.py test tests.catalog.benchmark_admin --settings=kronolearn.settings.development -v 2
```

1. Preparar mediante fixtures una base PostgreSQL desechable con 100 tracks y 50 modulos por track.
2. Ejecutar con configuracion, almacenamiento, indices y logging equivalentes a produccion sobre capacidad fija y documentada.
3. Enviar 20 solicitudes validas de calentamiento y excluirlas de todas las metricas.
4. Medir 200 solicitudes validas: 50 creaciones, 50 ediciones, 50 reordenamientos y 50 cambios de estado.
5. Medir en servidor desde la recepcion de cada solicitud hasta completar su respuesta, incluido el renderizado; excluir latencia de red publica y tiempo humano.
6. Registrar entorno, capacidad, configuracion, 200 observaciones y percentil 95 por mezcla total y familia de operacion.

Esperado: el percentil 95 de las 200 solicitudes medidas es menor de 2 segundos y el reporte permite reproducir la muestra exacta. Las 20 solicitudes de calentamiento no cuentan como observaciones.

## Evidencia de aceptacion

Conservar para revision:

- salida de CI y de las pruebas PostgreSQL con todos los gates en verde;
- nombres de pruebas que cubren cada grupo de FR en [contracts/web.md](contracts/web.md#matriz-de-cobertura);
- capturas con datos locales no sensibles de listas administrativas, formularios con error y catalogo del aprendiz;
- aserciones agregadas de posiciones, versiones y auditoria, sin secretos ni referencias crudas fallidas;
- hoja agregada de tres participantes con duracion, finalizacion, identificacion de estado/orden y resultado de la ronda de colision;
- reporte reproducible de rendimiento para SC-008.
