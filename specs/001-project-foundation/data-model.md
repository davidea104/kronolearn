# data-model.md

**Propósito**: Identificar entidades clave y límites de dominio para el monolito inicial.

## Entidades iniciales (alto nivel)

- User / Learner (accounts): id, username, email, roles, metadata (no incluir atributos sensibles sin control).
- Track (catalog): id, title, description, version, author, source, status, published_at.
- Module: id, track_id, title, content_version.
- Microlesson / Case: id, module_id, type, content_version.
- Attempt (learning/gamification): id, user_id, item_id, attempt_number, score, timestamp, content_version.
- Progress: id, user_id, track_id, progress_percentage, last_attempt_id.
- WeeklyLeaderboardEntry (analytics/gamification): user_id, week_start, rank, points_snapshot.

## Bounded Contexts

- accounts: autenticación, perfiles, roles y permisos.
- catalog: gestión de contenido (tracks, módulos, versiones).
- learning: flujo de sesiones, selección de siguiente sesión, intentos.
- gamification: cálculo de puntos, rachas, eventos de puntuación.
- analytics: generación de rankings y métricas, snapshots semanales.
- ui: vistas y componentes (no lógica de dominio).

## Notas sobre integridad y idempotencia

- Los intentos y eventos de puntuación DEBEN registrar la versión del contenido presentado.
- Las operaciones que actualizan progreso y generan eventos DEBEN diseñarse para ser idempotentes y ejecutarse
+transaccionalmente en la implementación.
