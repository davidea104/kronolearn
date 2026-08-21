# Checklist de calidad de requisitos: Seguridad y ciclo editorial

**Purpose**: Evaluar claridad, completitud y consistencia de los requisitos de autorizacion, no divulgacion, versionado y auditoria antes de generar `tasks.md`.
**Created**: 2026-08-21
**Feature**: [spec.md](../spec.md)

**Note**: Esta checklist personalizada fue generada por `/speckit-checklist` a partir del contexto y los requisitos del feature.
**Review Ownership**: Esta checklist pertenece al revisor como artefacto de calidad de requisitos. Un item se marca `[x]` solo cuando el revisor determina que el criterio de calidad esta satisfecho.
**Marker Semantics**: `[x]` significa que el criterio fue revisado y aprobado respecto de la calidad de los requisitos. No significa que el trabajo de implementacion este completo.

## Completitud de requisitos

- [ ] CHK001 - Esta documentada la matriz completa de acceso para cuenta anonima, cuenta inactiva, aprendiz, administrador de contenido, cuenta con ambos roles y superusuario sin `content_admin`? [Completeness, Spec §FR-001, Contract §Respuestas de acceso]
- [ ] CHK002 - Estan definidos los campos que pueden conocer aprendices y administradores, incluidos los campos que nunca deben cruzar cada frontera de presentacion? [Completeness, Spec §FR-012/013, Contract §Catalogo del aprendiz]
- [ ] CHK003 - Estan especificados los metadatos y efectos de version para primera activacion, reactivacion, edicion activa, edicion inactiva y desactivacion de tracks y modulos? [Completeness, Spec §FR-005/009/015]
- [ ] CHK004 - Esta delimitado que intentos producen auditoria y cuales se detienen en autenticacion o CSRF antes de constituir un comando de dominio? [Completeness, Spec §FR-016, Contract §Respuestas de acceso]
- [ ] CHK005 - Estan definidos la retencion, consulta autorizada y vinculo futuro de versiones publicadas con referencias historicas de aprendizaje? [Completeness, Spec §FR-015/017, Gap]
- [ ] CHK006 - Estan documentados requisitos de accesibilidad para formularios, errores, conflictos, cambios de estado y reordenamientos tanto en HTML completo como en fragmentos HTMX? [Completeness, Contract §Reglas globales, Gap]

## Claridad de requisitos

- [ ] CHK007 - Esta definido si `source` admite texto libre, una URL o una referencia con formato verificable, y que mensaje corresponde a cada valor invalido? [Clarity, Spec §FR-015, Model §TrackVersion/ModuleVersion, Ambiguity]
- [ ] CHK008 - Esta aclarado si reactivar un elemento sin cambios desde su ultima publicacion crea una version nueva o conserva la anterior? [Clarity, Spec §FR-015, Contract §Estado de track/Estado de modulo, Ambiguity]
- [ ] CHK009 - Esta definido si una edicion activa sin cambios materiales es una publicacion aceptada, una operacion idempotente o una validacion rechazada? [Clarity, Spec §FR-015/016, Ambiguity]
- [ ] CHK010 - Se especifica que propiedades observables deben ser equivalentes entre contenido inexistente, inactivo, perteneciente a otro padre y no autorizado para cumplir la no divulgacion? [Clarity, Spec §FR-012/013, Contract §Respuestas de acceso]
- [ ] CHK011 - Estan diferenciados el alcance, emision y vigencia de `revision`, `track_order_revision` y `module_order_revision`, incluida la revision que debe usarse despues de un conflicto? [Clarity, Spec §FR-018, Model §Convenciones]
- [ ] CHK012 - La equivalencia de titulos define de manera inequivoca trim, `casefold`, tratamiento Unicode y alcance global o por track? [Clarity, Spec §FR-019, Research §Decision 4]

## Consistencia entre artefactos

- [ ] CHK013 - Es consistente la promesa de auditar operaciones rechazadas con la exclusion contractual de solicitudes anonimas o con CSRF invalido que no alcanzan el servicio? [Consistency, Spec §AC-FR-016, Contract §Respuestas de acceso]
- [ ] CHK014 - La definicion constitucional de conservar la version exacta presentada es consistente con snapshots que excluyen posicion, estado, pertenencia y orden de la jerarquia? [Consistency, Constitution §10, Spec §FR-015/017, Model §Relaciones]
- [ ] CHK015 - La restriccion de no desactivar el ultimo modulo activo de un track activo esta alineada con todos los requisitos de cambio de estado y con la condicion de activacion del track? [Consistency, Spec §FR-005/009, Research §Decision 11]
- [ ] CHK016 - La exigencia exclusiva de `CONTENT_ADMIN_ROLE` es consistente con las capacidades esperadas de un superusuario de plataforma y de una cuenta con roles acumulados? [Consistency, Spec §FR-001, Contract §Reglas globales, Assumption]
- [ ] CHK017 - Estan alineadas las respuestas de exito, validacion y conflicto entre HTML y HTMX para crear, editar, activar, desactivar y reordenar? [Consistency, Contract §Reglas globales/Matriz de resultados administrativos]

## Calidad de criterios de aceptacion

- [ ] CHK018 - Puede evaluarse objetivamente la no divulgacion mediante criterios sobre estado, cuerpo, campos, mensajes y diferencias temporales permitidas? [Measurability, Spec §AC-FR-001/013, Spec §AC-FR-010/011/012]
- [ ] CHK019 - Los criterios editoriales cubren valores ausentes, fecha futura, formato de fecha, estado distinto de `APPROVED`, fuente fuera de limite y metadata manipulada por el navegador? [Acceptance Criteria, Spec §AC-FR-015, Contract §Editar track]
- [ ] CHK020 - La inmutabilidad tiene criterios objetivos para cambios desde servicios, administracion, relaciones protegidas y accesos directos, ademas de conservar numeros previos? [Acceptance Criteria, Spec §AC-FR-015/017, Model §TrackVersion/ModuleVersion]
- [ ] CHK021 - SC-008 define suficientemente el conjunto de operaciones, distribucion de datos, concurrencia, entorno de medida y punto inicial/final de la latencia para reproducir el percentil? [Measurability, Spec §SC-008, Quickstart §Comprobacion de rendimiento]

## Cobertura de escenarios

- [ ] CHK022 - El flujo principal documenta de forma completa la secuencia crear track, crear modulo, publicar modulo, publicar track y exponer solo la jerarquia activa? [Coverage, Spec §User Story 1/2/3]
- [ ] CHK023 - El flujo alternativo de modulo activo bajo track inactivo define con claridad su version publicada, visibilidad y comportamiento al activar posteriormente el track? [Coverage, Spec §Edge Cases, Spec §FR-009/012/015]
- [ ] CHK024 - Los requisitos cubren carreras entre edicion, activacion, desactivacion, reordenamiento y unicidad cuando comparten una revision inicial? [Coverage, Exception Flow, Spec §FR-018/019]
- [ ] CHK025 - El flujo de recuperacion tras `409` define que datos puede conservar el formulario, que debe recargarse y como se obtiene un token vigente sin repetir una publicacion? [Coverage, Recovery, Spec §FR-018, Contract §Editar track]
- [ ] CHK026 - Esta definido el resultado de una falla tecnica durante una mutacion respecto de rollback, version, orden y presencia o ausencia de auditoria? [Coverage, Recovery, Model §Resultado de comandos, Gap]

## Cobertura de casos limite

- [ ] CHK027 - Estan definidos los estados vacios para catalogo sin tracks, track sin modulos y catalogo sin contenido activo, incluidas las acciones administrativas disponibles? [Edge Case, Gap]
- [ ] CHK028 - Los limites textuales especifican si se aplican antes o despues de trim y normalizacion, especialmente cuando `casefold` expande caracteres Unicode? [Edge Case, Research §Decision 4/12, Model §Convenciones]
- [ ] CHK029 - Se resuelve de manera determinista la carrera entre desactivar el ultimo modulo activo, desactivar el track y activar otro modulo? [Edge Case, Spec §FR-005/009/018, Research §Decision 11]

## Requisitos no funcionales

- [ ] CHK030 - Estan definidos foco, anuncio accesible, resumen de errores y recuperacion de teclado para todas las respuestas parciales y completas, no solo para reordenar tracks? [Accessibility, Contract §Reglas globales/Reordenar tracks, Gap]
- [ ] CHK031 - Estan documentados minimizacion, acceso, retencion y eventual purga legal de auditoria y metadata editorial sin debilitar la inmutabilidad requerida? [Security, Privacy, Spec §FR-015/016/017, Gap]
- [ ] CHK032 - El objetivo de rendimiento cubre por separado operaciones con bloqueo, renderizado completo y fragmentos HTMX bajo el volumen maximo declarado? [Performance, Spec §SC-008, Plan §Technical Context]

## Dependencias y supuestos

- [ ] CHK033 - Esta documentado como afecta a una sesion vigente la desactivacion de cuenta o revocacion de `content_admin`, incluido el siguiente GET y POST administrativo? [Dependency, Spec §Dependencies, Contract §Respuestas de acceso]
- [ ] CHK034 - Existe un contrato suficientemente definido para que features futuras de aprendizaje conserven y consulten la version exacta presentada sin depender del registro mutable? [Dependency, Constitution §10, Spec §FR-017, Gap]

## Ambiguedades y conflictos pendientes

- [ ] CHK035 - Esta resuelta la tension entre identificar el elemento afectado en toda auditoria y no almacenar una referencia cruda cuando el UUID es inexistente o malformado? [Conflict, Spec §FR-016, Model §CatalogChangeLog, Contract §Matriz de resultados administrativos]
- [ ] CHK036 - Esta definida la precedencia entre idempotencia y conflicto cuando se repite un POST exitoso con el token que quedo obsoleto por la primera solicitud? [Ambiguity, Spec §FR-018, Contract §Matriz de resultados administrativos]

## Notes

- Marcar un item `[x]` solo cuando la revision confirme que el criterio de calidad de requisitos esta satisfecho.
- Dejar el item sin marcar cuando requiera aclaracion, correccion o evaluacion del revisor.
- `/speckit-implement` lee el estado de la checklist como gate y no modifica los marcadores.
- `checklists/requirements.md` conserva su ciclo separado, administrado por `/speckit-specify` y `/speckit-clarify`.
- Agregar comentarios o hallazgos inline y enlazar recursos relevantes cuando corresponda.
- Los IDs son globales y secuenciales dentro de este archivo.
