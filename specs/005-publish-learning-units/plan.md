# Implementation Plan: Publicacion de unidades de aprendizaje

**Branch**: `005-publish-learning-units` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-publish-learning-units/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Publicar diez unidades trazables y ordenadas, siete en el track principal y tres en el secundario, mediante una carga de despliegue atomica, repetible y segura ante concurrencia. El corpus aprobado reside en JSON versionado y se convierte en definiciones inmutables antes de cualquier escritura. `accounts` resuelve y autoriza la identidad configurada por el servidor, `catalog.services.content` conserva las mutaciones y la reconciliacion, y un comando Django sin argumentos de identidad actua como adaptador fino. Se agrega el estado editorial explicito a `ContentVersion` mediante una migracion de catalogo y se documenta la ejecucion en Railway sin modificar `seed_demo` ni construir interfaz.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 5.2.17, psycopg 3.3.4; sin dependencias nuevas

**Storage**: PostgreSQL 16 como backend autoritativo; SQLite en memoria solo para pruebas portables

**Testing**: Django `TestCase` y `TransactionTestCase`, `ThreadPoolExecutor` con conexiones separadas para concurrencia PostgreSQL, Ruff 0.16.3

**Target Platform**: Aplicacion Django desplegada en Railway sobre Linux; comando ejecutado como paso de despliegue

**Project Type**: Monolito web modular con servicio de dominio y adaptador CLI de administracion

**Performance Goals**: Reconciliar el conjunto acotado de 2 tracks, 2 modulos y 10 unidades en una transaccion; dos ejecuciones simultaneas deben converger sin reintentos manuales ni duplicados

**Constraints**: Sin frontend, endpoints, workers ni nueva infraestructura; snapshots append-only; carga total atomica; segunda ejecucion sin escrituras; corpus JSON no ejecutable; identidad desde `CONTENT_AUTHOR_ACCOUNT_ID` en configuracion privada; salida sin datos de cuenta; `seed_demo` permanece intacto

**Scale/Scope**: 10 unidades, 2 tracks, 2 modulos, 30 a 40 opciones vigentes, 7 laboratorios vigentes y como maximo 2 ejecuciones concurrentes en la matriz de aceptacion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

La evaluacion referencia la constitucion vigente sin reproducir sus reglas.

| Referencia | Evidencia de diseño | Pre-Phase 0 | Post-Phase 1 |
| --- | --- | --- | --- |
| Principio 1 | Spec aclarada, criterios verificables y artefactos de plan separados de la implementacion. | PASS | PASS |
| Principios 2 y 3 | Mutaciones y reconciliacion en `catalog.services.content`; comando fino y corpus JSON versionado separado del codigo ejecutable. | PASS | PASS |
| Principio 5 | Transaccion exterior, lock `CatalogState`, revisiones y restricciones unicas existentes. | PASS | PASS |
| Principio 6 | Matriz portable y pruebas de concurrencia PostgreSQL definidas en [quickstart.md](quickstart.md). | PASS | PASS |
| Principios 8 y 9 | Cambio limitado al modulo `catalog`, sin infraestructura ni interfaz nueva. | PASS | PASS |
| Principio 10 | `ContentVersion.editorial_status` persiste `PUBLISHED`; versiones, opciones y laboratorios permanecen append-only. | PASS | PASS |
| Principios 12 a 14 | Identidad no interactiva desde configuracion privada, resolucion mediante servicio publicado de `accounts` y salida minimizada. | PASS | PASS |
| Principio 16 | Manifiesto cerrado abajo; la migracion `catalog/0003` es indispensable y debe coordinarse como unica migracion activa de la app. | PASS | PASS |

**Gate result**: PASS antes de Phase 0 y PASS despues del diseño de Phase 1. No hay excepciones constitucionales.

## Project Structure

### Documentation (this feature)

```text
specs/005-publish-learning-units/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   ├── account-query-service.md
│   ├── content-services.md
│   └── load-learning-content-command.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
```text
accounts/
└── services/
    └── queries.py                         # CREATE: resolver y autorizar cuenta de despliegue

catalog/
├── models.py                              # MODIFY: estado editorial de ContentVersion
├── migrations/
│   └── 0003_contentversion_editorial_status.py  # CREATE: campo y constraint PUBLISHED
├── services/
│   └── content.py                         # MODIFY: publicar, crear borrador y reconciliar
├── content_data/
│   ├── __init__.py                        # CREATE: API de carga de definiciones
│   ├── definitions.py                     # CREATE: dataclasses y parser/validacion del JSON
│   └── learning_units.json                # CREATE: corpus editorial autoritativo 7/3
└── management/
    ├── __init__.py                        # CREATE
    └── commands/
        ├── __init__.py                    # CREATE
        └── load_learning_content.py       # CREATE: adaptador de despliegue

    tests/accounts/
    └── test_queries.py                        # CREATE: resolucion, bloqueo y autorizacion generica

tests/catalog/
├── test_domain_contracts.py               # MODIFY: servicios dejan de ser STUB
├── test_models.py                          # MODIFY: estado editorial inmutable
├── test_migrations.py                      # CREATE: backfill y constraint de 0003
├── test_content_publication.py            # CREATE: payloads, permisos y versionado
├── test_learning_content_data.py           # CREATE: definicion 7/3, opciones y labs
├── test_learning_content_load.py           # CREATE: reconciliacion, rollback y concurrencia
└── test_load_learning_content_command.py   # CREATE: contrato CLI y privacidad

kronolearn/settings/base.py                 # MODIFY: configuracion privada de cuenta autora
.env.example                                # MODIFY: nombre de variable sin valor real
docs/deployment/railway.md                  # MODIFY: migrar, cargar y arrancar
```

**Structure Decision**: Conservar el monolito Django. `content_data/learning_units.json` es la fuente editorial no ejecutable; `definitions.py` la parsea a estructuras inmutables sin ORM. `accounts.services.queries` posee la lectura y autorizacion de cuentas, mientras `catalog.services.content` posee validacion de contenido, locks y escrituras. El comando lee solo configuracion Django, carga el JSON e invoca el servicio. Las pruebas permanecen junto al modulo propietario.

### Closed File Manifest

Solo pueden modificarse o crearse los archivos enumerados en el arbol de Source Code. En `catalog/models.py` el unico cambio permitido es `ContentVersion.editorial_status` y su constraint; la unica migracion permitida es la nueva `catalog/0003` correspondiente. Las migraciones existentes, `ui/management/commands/seed_demo.py`, `kronolearn/urls.py`, `templates/`, CI y todos los artefactos de feature 004 quedan cerrados. `docs/deployment/railway.md`, `.env.example` y `kronolearn/settings/base.py` solo pueden cambiar para configurar y documentar la identidad de despliegue y el orden `migrate -> load_learning_content -> start`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No aplica: no se identificaron violaciones que requieran excepcion.
