# Feature Ownership Contract

## Rules

1. Feature 004 creates all baseline models, migrations, public signatures, event definitions, root composition, and shared UI extension points.
2. After merge, a feature edits only its assigned paths and consumes shared contracts without changing them.
3. Only one feature per Django app may add migrations. Any later schema need requires an explicit coordinated contract amendment.
4. Frozen paths cannot be edited merely to add an import, route, navigation link, model field, or convenience re-export.
5. Read dependencies cross apps through published query services. Reactions to attempts and completed sessions cross apps through `attempt_registered` and `session_completed`.
6. `gamification` is the sole writer of `SeasonParticipation`; `learning` emits facts and never writes that model directly.

## Frozen Shared Paths

```text
catalog/models.py
catalog/migrations/0002_domain_content.py
learning/models.py
learning/migrations/0001_initial.py
learning/signals.py
gamification/models.py
gamification/migrations/0001_initial.py
kronolearn/urls.py
ui/templates/base.html
ui/navigation.py
accounts/nav.py
catalog/nav.py
learning/nav.py
gamification/nav.py
analytics/nav.py
ui/nav.py
learning/urls/__init__.py
gamification/urls.py
analytics/urls.py
```

## Baseline Feature Matrix

| Feature | May modify | Must not modify |
| --- | --- | --- |
| Autoría de contenido | `catalog/services/content.py`, `templates/catalog/content/**`, `tests/catalog/content/**` | Models, migrations, root URLs, base template |
| Inscripción | `learning/services/enrollment.py`, `learning/urls/enrollment.py`, `learning/views/enrollment/**`, `templates/learning/enrollment/**`, `tests/learning/enrollment/**` | Other learning areas and frozen paths |
| Sesión diaria | `learning/services/session.py`, `learning/urls/session.py`, `learning/views/session/**`, `templates/learning/session/**`, `tests/learning/session/**` | Other learning areas, frozen paths, and `SeasonParticipation` |
| Intento y retroalimentación | `learning/services/attempts.py`, `learning/urls/attempts.py`, `learning/views/attempts/**`, `templates/learning/attempts/**`, `tests/learning/attempts/**` | Signal definition, models, other learning areas |
| Ruta y progreso | `learning/services/progress.py`, `learning/receivers.py`, `learning/urls/progress.py`, `learning/views/progress/**`, `templates/learning/progress/**`, `tests/learning/progress/**` | Signal definition, models, other learning areas |
| Puntos, racha y participación | `gamification/services/scoring.py`, `gamification/services/streaks.py`, `gamification/receivers.py`, `templates/gamification/**`, `tests/gamification/scoring/**`, `tests/gamification/streaks/**` | Models, migrations, root composition |

The two receiver-owning features coordinate edits by separate functions and tests in their assigned receiver module; if both would edit the same lines, points and streak owns `gamification/receivers.py` as one feature rather than splitting it.

## Backlog Reservations

| Feature | Reserved paths | Existing contracts consumed |
| --- | --- | --- |
| Liga semanal | `gamification/services/seasons.py`, leaderboard views/templates/tests | WeeklySeason, SeasonParticipation, LeaderboardEntry |
| Métricas administrativas | `analytics/services/metrics.py`, analytics views/templates/tests | ContentMetrics, EngagementMetrics, published query services |
| Insignias | New gamification-owned service/view/test paths approved before work | Attempt, Progress, ScoreEvent, Streak query contracts |
| Repaso | New learning-owned service/view/test paths approved before work | Attempt and Progress query contracts |
| Meta semanal | New gamification-owned service/view/test paths approved before work | SeasonParticipation query contract |

Backlog reservation does not authorize a migration. If a backlog feature needs persistent state not represented in the baseline, it must amend this contract and coordinate migration ownership before implementation.

## Contract Authority Lifecycle

During planning, `spec.md` and the approved files under `specs/004-domain-contracts/contracts/` are design inputs. Implementation code must conform to them. At feature completion, `docs/contracts/domain-contracts.md` becomes the single human source of truth. Automated drift tests compare it with executable public symbols, all six baseline ownership assignments, all five backlog traces, and frozen ownership entries; timed human review is not an acceptance dependency.
