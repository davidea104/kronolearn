# Changelog

Todos los cambios publicos relevantes de KronoLearn se documentan en este archivo.

## Unreleased

### Added

- Registro e inicio de sesion por correo canonico con cierre de sesion POST protegido por CSRF.
- Perfil propio privado que permite editar unicamente el nombre visible.
- Roles acumulativos `learner` y `content_admin`, gestionados por administradores de plataforma.
- Auditoria inmutable para cada intento autenticado de asignar o retirar el rol de contenido.
- Throttling persistente y progresivo por cuenta declarada y origen pseudonimizados.
- Pipeline CI con PostgreSQL 16, lint, formato, checks Django, drift de migraciones y suite completa.
- Administración de tracks y módulos con ordenamiento optimista, publicación versionada, auditoría inmutable y mejora progresiva HTMX.
- Catálogo del aprendiz que proyecta únicamente tracks y módulos activos en su orden vigente.
- Contratos compartidos para contenido versionado, inscripción, intentos, progreso, puntuación, rachas, temporadas y métricas, con 11 entidades y 20 interfaces públicas.
- Señales síncronas `attempt_registered` y `session_completed`, navegación distribuida, namespaces reservados y bloques estables de plantilla para features paralelas.
- Comando idempotente `seed_demo` con dos tracks publicados, cuentas privadas `.invalid`, datos de ejemplo válidos y barrera explícita fuera de desarrollo.
- Jobs CI separados para contratos portables en SQLite y evidencia autoritativa de migraciones, exclusión, concurrencia y privacidad en PostgreSQL 16.

### Changed

- La identidad principal usa `accounts.Account`, UUID y correo unico en lugar del modelo de usuario predeterminado de Django.
- Tracks y módulos se desactivan sin eliminación permanente; cada reactivación real y edición activa conserva un nuevo snapshot publicado.
- Los modelos, migraciones base, señales, composición raíz, navegación y plantilla compartida quedan congelados bajo `docs/contracts/domain-contracts.md`; esta entrega no añade flujos funcionales de aprendizaje ni administración.

### Migration

- `AUTH_USER_MODEL = "accounts.Account"` debe estar configurado antes de ejecutar la primera migracion del proyecto.
- Los entornos que ya tengan tablas creadas con el usuario predeterminado de Django deben recrear una base vacia o seguir un plan de migracion de datos especifico antes de desplegar esta version. No se admite cambiar el modelo de usuario in-place como parte de esta feature.
- Aplicar `catalog.0001_initial` crea las entidades del catálogo, constraints, índices y el singleton `CatalogState(id=1)` requerido para serializar el orden global.
- Aplicar `catalog.0002_domain_content`, `learning.0001_initial` y `gamification.0001_initial` crea la línea base compartida; PostgreSQL añade la exclusión de temporadas semanales no solapadas.
