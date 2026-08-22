# Quickstart Validation: Contratos y esqueleto de dominio

**Purpose**: Validar la infraestructura compartida despues de implementarla, sin depender de una feature funcional posterior.  
**Spec**: [spec.md](spec.md)  
**Data model**: [data-model.md](data-model.md)  
**Contracts**: [contracts/services.md](contracts/services.md), [contracts/domain-events.md](contracts/domain-events.md), [contracts/integration-surfaces.md](contracts/integration-surfaces.md), [contracts/ownership.md](contracts/ownership.md)

## Prerrequisitos

- Python 3.14.
- Dependencias bloqueadas de `requirements.txt`.
- PostgreSQL 16 local o compatible donde Django pueda crear y eliminar una base de pruebas.
- PowerShell abierto en la raiz del repositorio.
- Solo datos y credenciales locales; no usar produccion ni una base compartida.

Crear el entorno e instalar el lock si hace falta:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

## 1. Comprobaciones estaticas

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check --settings=kronolearn.settings.test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=kronolearn.settings.test
```

Esperado: todos los comandos terminan con codigo `0`; no hay cambios de modelo sin migracion ni errores de sistema.

## 2. Suite rapida con SQLite

La configuracion de prueba usa SQLite en memoria. Ejecutar los contratos portables:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.catalog.test_domain_contracts tests.learning tests.gamification tests.analytics tests.ui tests.integration.test_root_contracts tests.integration.test_seed_demo --settings=kronolearn.settings.test -v 2
```

Esperado:

- Se crean las 11 entidades y funcionan sus restricciones portables.
- Las versiones publicadas, opciones y laboratorios no pueden modificarse ni eliminarse.
- Las 20 firmas, sus tipos compuestos, estados STUB o IMPLEMENTAR y constantes coinciden con el contrato.
- Cada STUB lanza `NotImplementedError` sin escrituras.
- Las consultas implementadas devuelven orden determinista.
- La inspeccion de contratos y docstrings confirma las entradas canonicas y los propositos `learning.attempt.idempotency` y `gamification.score-event.idempotency`; pruebas directas de `security_digest` confirman determinismo y separacion entre propositos sin invocar productores STUB.
- Los receptores temporales reciben una vez los sobres `attempt_registered(attempt, result)` y `session_completed(enrollment, completed_at, idempotency_key)`; este último transporta un digest HMAC, no una clave cruda.
- Los harnesses transaccionales confirman orden síncrono, propagación de excepciones y rollback de sus propias escrituras; no invocan productores STUB ni afirman replay o reintento end-to-end.
- Los `dispatch_uid` impiden registros duplicados; `learning` se suscribe solo a `attempt_registered`, `gamification` se suscribe a ambos eventos y solo `gamification` declara escrituras futuras sobre `SeasonParticipation`.
- Los cuatro namespaces, los cinco bloques de plantilla, las carpetas reservadas y la navegacion distribuida estan disponibles.
- El HTML renderizado conserva un elemento `nav` semantico y las reglas o clases de foco visible para teclado mediante assertions automatizadas rapidas, sin navegador ni revision manual.
- La salida capturada no contiene contrasenas, correos, IP, tokens ni claves de idempotencia en claro; los dos correos demo `.invalid` solo existen en sus registros `Account`.

SQLite acelera el ciclo local, pero no demuestra exclusiones PostgreSQL, concurrencia real, migraciones de produccion ni auditoria de persistencia.

## 3. Suite autoritativa con PostgreSQL

Definir el entorno del proceso actual. Usar una base desechable y una clave solo local:

```powershell
$env:DJANGO_SETTINGS_MODULE = "kronolearn.settings.development"
$env:SECRET_KEY = "local-only-secret-key-change-me"
$env:DEBUG = "True"
$env:DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/kronolearn"
```

Validar una aplicacion completa desde cero:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py showmigrations catalog learning gamification
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Esperado: `catalog.0002_domain_content`, `learning.0001_initial` y `gamification.0001_initial` aparecen aplicadas; no se generan migraciones adicionales.

Ejecutar toda la suite con el backend equivalente a produccion:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.catalog.test_domain_contracts tests.learning tests.gamification tests.analytics tests.ui tests.integration --settings=kronolearn.settings.development -v 2
```

Esta ejecucion es la unica evidencia aceptable de:

- Grafo de migraciones sobre una base vacia.
- Restriccion de exclusion para temporadas no solapadas.
- Dos procesos resolviendo una temporada concurrente a la misma identidad logica.
- Unicidad concurrente de inscripcion, primer intento puntuable y digests de idempotencia.
- Propagacion y rollback total de las escrituras creadas por cada harness cuando falla un receptor.
- Restricciones persistentes sobre digests de intentos y eventos, sin atribuir replay o reintento a productores que permanecen como STUB.
- La forma `session_completed`, monto cero y ausencia de intento es aceptada por persistencia, pero no se impone mediante un constraint especifico de causa; esa combinacion pertenece al receptor futuro.
- Ausencia de datos sensibles en persistencia, auditoria y salidas capturadas.

## 4. Datos demo e idempotencia

Sobre la base PostgreSQL desechable de desarrollo:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py test tests.integration.test_seed_demo --settings=kronolearn.settings.development -v 2
```

Esperado despues de ambas ejecuciones:

- Existen los tracks publicados `Crea tu registro de gastos con agentes y SDD` y `Fundamentos de negocio para equipos técnicos`.
- Cada track tiene al menos un modulo publicado.
- Hay exactamente dos contenidos publicados, cada uno con una version vigente, opciones validas y un laboratorio.
- Hay exactamente una cuenta learner y una cuenta content_admin con direcciones deterministas no personales bajo `.invalid`, conservadas solo en sus filas `Account`, además de una temporada semanal vigente.
- Las identidades logicas y cantidades permanecen iguales; solo se repara data demo reconocible e incompleta.
- La salida muestra conteos y titulos publicos, nunca correos demo, credenciales ni identificadores privados.

Probar tambien la barrera fuera de desarrollo en una base desechable separada:

```powershell
$env:DEBUG = "False"
.\.venv\Scripts\python.exe manage.py seed_demo
```

Esperado: el comando termina con error antes de escribir. La variante con `--confirm-production` solo se valida de forma automatizada y debe crear contrasenas inutilizables sin imprimir credenciales.

## 5. Suite completa del repositorio

Restaurar el entorno de desarrollo y ejecutar todos los gates:

```powershell
$env:DEBUG = "True"
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m unittest tests.db.test_db_connection -v
```

Esperado: cada comando termina con codigo `0` y los flujos existentes de cuentas y catalogo conservan su comportamiento.

## Matriz de evidencia

| Evidencia | SQLite | PostgreSQL 16 |
| --- | --- | --- |
| Firmas, constantes, STUBs y proyecciones | Requerida | Requerida |
| Restricciones portables e inmutabilidad | Requerida | Requerida |
| URLs, plantilla y navegacion | Requerida | Requerida |
| Dos sobres de evento y registro unico | Requerida | Requerida |
| Seed idempotente y privacidad de salida | Requerida | Requerida |
| Migraciones desde cero | Suplementaria | Autoritativa |
| Exclusiones y concurrencia | No aplica | Autoritativa |
| Rollback transaccional multi-receptor | Suplementaria | Autoritativa |
| Auditoria y privacidad persistida | Suplementaria | Autoritativa |

La feature no queda aceptada con resultados exclusivamente SQLite.

## Autoridad y drift documental

Durante la implementacion, comparar el codigo con `spec.md` y los contratos aprobados bajo `specs/004-domain-contracts/contracts/`. Al terminar, ejecutar las pruebas de drift que confirman que `docs/contracts/domain-contracts.md` contiene las 11 entidades, 20 firmas, cinco proyecciones, dos sobres de evento, namespaces, bloques, las seis asignaciones de linea base y las cinco trazas de backlog. Desde ese punto, ese documento es la fuente humana unica para features consumidoras; la aceptacion de ownership y trazabilidad es automatizada y no depende de revisiones humanas cronometradas.

Ejecutar el gate enfocado de autoridad y ownership:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.integration.test_root_contracts --settings=kronolearn.settings.test -v 2
```

Esperado: las seis asignaciones editables son disjuntas, las cinco reservas de backlog tienen un contrato de lectura, cada app de dominio tiene un único propietario de migración, `SeasonParticipation` conserva un único escritor y el manifiesto `tasks.md` no aparece entre las superficies congeladas.
