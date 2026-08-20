# PostgreSQL local y en Railway

KronoLearn usa PostgreSQL y recibe su cadena de conexión mediante `DATABASE_URL`. La aplicación y las pruebas nunca deben registrar el valor de esta variable, ya que contiene credenciales.

## Desarrollo local

Se recomienda usar una instancia local de PostgreSQL 16 o una versión compatible, con una base y un usuario dedicados a KronoLearn. Configure la variable en un archivo `.env` local que no se versiona:

```env
DATABASE_URL=postgresql://kronolearn:CAMBIAR_ESTA_CLAVE@127.0.0.1:5432/kronolearn_db
```

La URL debe usar el esquema `postgresql://` (también se acepta el alias `postgres://`) e incluir host, puerto y nombre de base de datos. La prueba no crea tablas, usuarios ni bases de datos; solo abre una conexión y ejecuta `SELECT 1`.

## Railway

1. Cree o vincule un servicio PostgreSQL en el proyecto de Railway.
2. Referencie la variable `DATABASE_URL` que Railway proporciona al servicio web de KronoLearn.
3. No copie su valor al repositorio, archivos versionados ni logs de CI.
4. Use la URL entregada por Railway sin reemplazar host, puerto o parámetros TLS. Railway determina los requisitos de conexión según la red y el entorno del servicio.

## Validar la conexión

Con el entorno virtual instalado y `DATABASE_URL` presente en el proceso, ejecute:

```sh
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

La prueba falla con un mensaje explícito cuando falta `DATABASE_URL`, cuando su esquema no es PostgreSQL, o si no puede conectar o ejecutar la consulta básica. Para cargar un `.env` local en una sesión de shell compatible:

```sh
set -a; source .env; set +a
.venv/bin/python -m unittest tests.db.test_db_connection -v
```

Antes de ejecutar la prueba, compruebe que PostgreSQL está disponible y que el usuario de la URL tiene permiso de conexión a la base indicada.

## Diagnóstico

- **`DATABASE_URL` ausente**: defínala en el entorno local o confirme que Railway la referencia en el servicio web.
- **Esquema inválido**: use `postgresql://` o `postgres://`.
- **Conexión rechazada o timeout**: revise que el servidor, host, puerto, credenciales y reglas de red sean correctos.
- **Autenticación fallida**: renueve las credenciales fuera del repositorio y actualice la variable correspondiente.
