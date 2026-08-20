# Estrategia mínima de pruebas

## Runner y organización

La línea base utiliza el runner integrado de Django y `django.test.TestCase` como clase inicial para pruebas unitarias
que requieran aislamiento de base de datos. Las pruebas se ejecutarán con:

```sh
python3 manage.py test
```

La estructura objetivo mantiene los niveles definidos en el plan:

```text
tests/
├── unit/          # servicios y reglas de dominio
├── integration/   # límites entre apps, persistencia y contratos
└── smoke/         # arranque y endpoints públicos mínimos
```

Cada app también podrá alojar pruebas cercanas a su código mientras se conserve esta clasificación lógica.

## Cobertura mínima por fase

- Unitarias: servicios de dominio, validadores y transformaciones deterministas.
- Integración: persistencia, límites entre apps y contratos versionados cuando se implementen.
- Smoke: arranque y rutas públicas esenciales. La prueba de `/healthz` está implementada en `tests/smoke/test_health_check.py` y se ejecuta en CI.

Las reglas críticas exigidas por la constitución —puntos, rachas, primer intento, idempotencia, progreso,
publicación/versionado, permisos, siguiente sesión y liga semanal— deberán contar con pruebas automatizadas antes de
que se incorporen sus implementaciones.

## Calidad local y gate de merge

Ruff es la herramienta única de lint y formato para Python:

```sh
ruff check .
ruff format --check .
python3 manage.py test
```

Estas comprobaciones se ejecutan en GitHub Actions mediante `.github/workflows/ci.yml` y bloquean la integración cuando alguna termina con un código distinto de cero.

## Criterio de mantenimiento

Una prueba debe describir comportamiento observable, no detalles internos. Las correcciones de defectos deben incluir
una prueba de regresión. Los cambios a contratos públicos o reglas de dominio deben actualizar sus pruebas en el mismo
cambio.
