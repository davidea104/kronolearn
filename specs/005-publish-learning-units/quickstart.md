# Quickstart Validation: Publicacion de unidades de aprendizaje

**Purpose**: Validar servicios, datos y comando de despliegue despues de implementar feature 005.  
**Spec**: [spec.md](spec.md)  
**Data model**: [data-model.md](data-model.md)  
**Contracts**: [content-services.md](contracts/content-services.md), [load-learning-content-command.md](contracts/load-learning-content-command.md)

## Prerrequisitos

- Python 3.14 y dependencias bloqueadas de `requirements.txt`.
- PowerShell abierto en la raiz del repositorio.
- PostgreSQL 16 local o compatible, con permiso para crear una base de pruebas.
- Una base desechable; no usar produccion para estas comprobaciones.
- Una cuenta activa con rol `content_admin`, provisionada antes de la carga.
- Definir su referencia en `$env:CONTENT_AUTHOR_ACCOUNT_ID` como configuracion privada sin imprimirla ni incorporarla a logs.

Instalar el entorno cuando sea necesario:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

## 1. Comprobaciones estaticas

```powershell
.\.venv\Scripts\ruff.exe check accounts catalog kronolearn/settings tests/accounts tests/catalog
.\.venv\Scripts\ruff.exe format --check accounts catalog kronolearn/settings tests/accounts tests/catalog
.\.venv\Scripts\python.exe manage.py check --settings=kronolearn.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=kronolearn.settings.test
```

Esperado: todos terminan con codigo 0 y `makemigrations` confirma que la migracion `catalog/0003_contentversion_editorial_status.py` describe todo el estado del modelo sin drift adicional.

## 2. Suite portable con SQLite

```powershell
.\.venv\Scripts\python.exe manage.py test tests.accounts.test_queries tests.catalog.test_domain_contracts tests.catalog.test_content_publication tests.catalog.test_learning_content_data tests.catalog.test_load_learning_content_command --settings=kronolearn.settings.test -v 2
```

Esta suite debe demostrar:

- Firmas estables de `create_content_draft` y `publish_content_item`.
- Rechazo de actores no autorizados y revisiones obsoletas.
- Matriz de payloads invalidos sin versiones parciales.
- Versiones, opciones y laboratorios inmutables.
- Estado editorial `PUBLISHED` persistido y derivado por el servicio.
- Definicion fija con 2 tracks, 2 modulos, 10 unidades, orden 7/3, opciones 3/4 y laboratorios 7/0.
- Parser estricto del JSON y titulo secundario canonico con tilde, incluido el alias legacy sin tilde.
- Servicio de consulta de `accounts` y adaptador CLI sin consultas o escrituras ORM, argumentos de identidad ni salida con datos de cuenta.

SQLite acelera estos contratos, pero no constituye evidencia de concurrencia ni de locks de fila.

## 3. Suite autoritativa con PostgreSQL

Definir variables locales para una base desechable:

```powershell
$env:DJANGO_SETTINGS_MODULE = "kronolearn.settings.development"
$env:SECRET_KEY = "local-only-secret-key-change-me"
$env:DEBUG = "True"
$env:DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/kronolearn"
```

Aplicar y comprobar el esquema, incluida la migracion de estado editorial:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Ejecutar todas las pruebas de la feature sobre PostgreSQL:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.accounts.test_queries tests.catalog.test_content_publication tests.catalog.test_learning_content_data tests.catalog.test_learning_content_load tests.catalog.test_load_learning_content_command -v 2
```

Esperado:

- Dos creaciones de borrador concurrentes se serializan; una revision obsoleta no duplica posiciones.
- Dos publicaciones concurrentes sobre la misma revision crean una sola version.
- Dos cargas simultaneas terminan correctamente y dejan exactamente 2 tracks, 2 modulos, 10 unidades y un solo conjunto vigente de componentes.
- Una falla inyectada en cualquier etapa revierte tracks, modulos, unidades, versiones, opciones y laboratorios de toda la ejecucion.

## 4. Ejecucion del comando

Sobre la base desechable y con `$env:CONTENT_AUTHOR_ACCOUNT_ID` definido:

```powershell
.\.venv\Scripts\python.exe manage.py load_learning_content
.\.venv\Scripts\python.exe manage.py load_learning_content
```

Esperado:

- Ambos comandos terminan con codigo 0.
- La primera ejecucion informa el conjunto final 2/2/10 y las creaciones necesarias.
- La segunda informa cero unidades y cero versiones creadas.
- La segunda ejecucion no cambia IDs, revisiones, versiones vigentes ni fechas de publicacion.
- Ninguna salida contiene el UUID autor, correo, credenciales ni URL de base de datos.
- Invocar el comando con `--actor-id` se rechaza como argumento desconocido.

La compatibilidad con el estado legacy de feature 004 se valida de forma automatizada en `tests.catalog.test_learning_content_load`: despues de crear el grafo demo en una fixture, la carga conserva las dos unidades de posicion 1, publica como maximo una correccion por unidad y completa las ocho restantes. No se modifica ni se convierte `seed_demo` en parte del despliegue.

## 5. Conflictos y rollback

Ejecutar los casos enfocados de reconciliacion:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.catalog.test_learning_content_load -v 2
```

Esperado:

- Una unidad ajena en posicion esperada produce una colision y cero cambios.
- Una unidad adicional produce un conflicto y cero cambios.
- Una secuencia con huecos se rechaza.
- Un borrador vacio compatible puede completarse.
- Una version controlada distinta crea una unica version posterior y conserva la anterior.
- Una repeticion convergida crea y modifica cero registros.

## 6. Validacion editorial de cinco minutos

Realizar la revision de SC-007 con cinco aprendices pertenecientes a las audiencias objetivo. Cada unidad se prueba en una sesion separada y sin exposicion previa del contenido:

1. Iniciar el cronometro cuando se muestran el titulo, objetivo, microleccion, caso y opciones.
2. Detenerlo cuando el participante registra una opcion y explica su decision usando la consecuencia y explicacion mostradas.
3. Registrar un identificador anonimo de participante, unidad, duracion y si la explicacion identifica la decision optima.
4. Aprobar cada unidad solo si al menos cuatro de cinco participantes terminan en cinco minutos o menos y explican la decision optima.

El reporte editorial agregado se conserva como evidencia de aceptacion fuera de CI y no incluye cuentas, correos ni otros identificadores internos.

## 7. Regresion completa

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m unittest tests.db.test_db_connection -v
```

Esperado: todos los gates terminan con codigo 0, `seed_demo` y sus pruebas permanecen sin cambios, la migracion `catalog/0003_contentversion_editorial_status.py` se aplica correctamente y no aparece drift adicional.

## Matriz de evidencia

| Evidencia | SQLite | PostgreSQL 16 |
| --- | --- | --- |
| Firmas y payloads | Requerida | Requerida |
| Datos 7/3, opciones 3/4 y laboratorios 7/0 | Requerida | Requerida |
| Autorizacion y privacidad de salida | Requerida | Requerida |
| Migracion y estado editorial persistido | Suplementaria | Autoritativa |
| Inmutabilidad y versionado secuencial | Requerida | Requerida |
| Idempotencia consecutiva | Requerida | Requerida |
| Rollback de la carga completa | Suplementaria | Autoritativa |
| Locks y dos cargas simultaneas | No aplica | Autoritativa |
| Ausencia de drift de migraciones | Requerida | Requerida |

La feature no queda aceptada con resultados exclusivamente SQLite.