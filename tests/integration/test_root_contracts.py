"""Contract tests for shared route and import integration surfaces."""

import importlib
import inspect
from pathlib import Path

from django.test import SimpleTestCase
from django.urls import get_resolver

BASELINE_IMPORT_MATRIX = {
    "content-authoring": (
        "catalog.services.content",
        "catalog.models",
    ),
    "enrollment": (
        "learning.services.enrollment",
        "learning.urls.enrollment",
    ),
    "daily-session": (
        "learning.services.session",
        "learning.urls.session",
        "catalog.services.content",
    ),
    "attempt-feedback": (
        "learning.services.attempts",
        "learning.urls.attempts",
        "learning.signals",
    ),
    "route-progress": (
        "learning.services.progress",
        "learning.urls.progress",
        "learning.receivers",
    ),
    "points-streak-participation": (
        "gamification.services.scoring",
        "gamification.services.streaks",
        "gamification.receivers",
    ),
}

SERVICE_CONTRACTS = (
    (
        "catalog.services.content",
        "publish_content_item",
        ("content_item", "actor", "payload"),
        "STUB",
    ),
    (
        "catalog.services.content",
        "create_content_draft",
        ("module", "actor", "payload"),
        "STUB",
    ),
    (
        "catalog.services.content",
        "get_published_version",
        ("content_item",),
        "IMPLEMENT",
    ),
    ("catalog.services.content", "list_published_versions", ("track",), "IMPLEMENT"),
    ("learning.services.enrollment", "enroll", ("account", "track"), "STUB"),
    (
        "learning.services.enrollment",
        "get_enrollment",
        ("account", "track"),
        "IMPLEMENT",
    ),
    ("learning.services.enrollment", "list_enrollments", ("account",), "IMPLEMENT"),
    ("learning.services.session", "get_next_content_version", ("enrollment",), "STUB"),
    ("learning.services.session", "is_track_completed", ("enrollment",), "STUB"),
    (
        "learning.services.attempts",
        "register_attempt",
        ("enrollment", "content_version", "choice", "idempotency_key"),
        "STUB",
    ),
    ("learning.services.attempts", "list_attempts", ("enrollment",), "IMPLEMENT"),
    ("learning.services.progress", "recompute_progress", ("enrollment",), "STUB"),
    ("learning.services.progress", "get_track_progress", ("enrollment",), "STUB"),
    ("gamification.services.scoring", "award_for_attempt", ("attempt",), "STUB"),
    (
        "gamification.services.streaks",
        "register_activity",
        ("account", "activity_date"),
        "STUB",
    ),
    ("gamification.services.streaks", "streak_bonus", ("streak",), "STUB"),
    ("gamification.services.seasons", "current_season", ("moment",), "IMPLEMENT"),
    ("gamification.services.seasons", "leaderboard", ("season",), "STUB"),
    ("analytics.services.metrics", "content_metrics", ("track",), "STUB"),
    ("analytics.services.metrics", "engagement_metrics", ("window_days",), "STUB"),
)

BASELINE_OWNERSHIP = {
    "Autoría de contenido": {
        "catalog/services/content.py",
        "templates/catalog/content/**",
        "tests/catalog/content/**",
    },
    "Inscripción": {
        "learning/services/enrollment.py",
        "learning/urls/enrollment.py",
        "learning/views/enrollment/**",
        "templates/learning/enrollment/**",
        "tests/learning/enrollment/**",
    },
    "Sesión diaria": {
        "learning/services/session.py",
        "learning/urls/session.py",
        "learning/views/session/**",
        "templates/learning/session/**",
        "tests/learning/session/**",
    },
    "Intento y retroalimentación": {
        "learning/services/attempts.py",
        "learning/urls/attempts.py",
        "learning/views/attempts/**",
        "templates/learning/attempts/**",
        "tests/learning/attempts/**",
    },
    "Ruta y progreso": {
        "learning/services/progress.py",
        "learning/receivers.py",
        "learning/urls/progress.py",
        "learning/views/progress/**",
        "templates/learning/progress/**",
        "tests/learning/progress/**",
    },
    "Puntos, racha y participación": {
        "gamification/services/scoring.py",
        "gamification/services/streaks.py",
        "gamification/receivers.py",
        "templates/gamification/**",
        "tests/gamification/scoring/**",
        "tests/gamification/streaks/**",
    },
}

BACKLOG_TRACES = (
    "Liga semanal",
    "Métricas administrativas",
    "Insignias",
    "Repaso",
    "Meta semanal",
)

STUB_DOCSTRING_SECTIONS = (
    "Preconditions:",
    "Result:",
    "Ordering:",
    "Current effects:",
    "Expected errors:",
    "Future authorization:",
    "Idempotency:",
)


class RootContractTests(SimpleTestCase):
    def test_six_baseline_consumers_can_import_their_contracts(self):
        self.assertEqual(len(BASELINE_IMPORT_MATRIX), 6)
        for feature, module_names in BASELINE_IMPORT_MATRIX.items():
            for module_name in module_names:
                with self.subTest(feature=feature, module=module_name):
                    self.assertEqual(
                        importlib.import_module(module_name).__name__, module_name
                    )

    def test_shared_namespaces_are_composed_exactly_once(self):
        resolver = get_resolver()
        for namespace in ("catalog", "learning", "gamification", "analytics"):
            self.assertIn(namespace, resolver.namespace_dict)
            self.assertEqual(
                sum(
                    pattern.namespace == namespace
                    for pattern in resolver.url_patterns
                    if hasattr(pattern, "namespace")
                ),
                1,
            )

    def test_reserved_route_modules_have_no_workflow_routes(self):
        modules = (
            "learning.urls.enrollment",
            "learning.urls.session",
            "learning.urls.attempts",
            "learning.urls.progress",
            "gamification.urls",
            "analytics.urls",
        )
        for module_name in modules:
            module = importlib.import_module(module_name)
            self.assertEqual(module.urlpatterns, [], module_name)

    def test_package_initializers_remain_empty(self):
        root = Path(__file__).resolve().parents[2]
        for relative_path in (
            "learning/services/__init__.py",
            "learning/views/__init__.py",
            "gamification/services/__init__.py",
            "analytics/services/__init__.py",
        ):
            self.assertEqual((root / relative_path).read_text(encoding="utf-8"), "")

    def test_authoritative_document_tracks_executable_contracts(self):
        root = Path(__file__).resolve().parents[2]
        document = (root / "docs/contracts/domain-contracts.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(len(SERVICE_CONTRACTS), 20)
        for module_name, function_name, parameters, state in SERVICE_CONTRACTS:
            function = getattr(importlib.import_module(module_name), function_name)
            self.assertEqual(tuple(inspect.signature(function).parameters), parameters)
            signature = f"({', '.join(parameters)})"
            self.assertIn(f"| `{function_name}` | `{signature}` | {state} |", document)

        for model_name in (
            "ContentItem",
            "ContentVersion",
            "Choice",
            "LabExercise",
            "Enrollment",
            "Attempt",
            "Progress",
            "ScoreEvent",
            "Streak",
            "WeeklySeason",
            "SeasonParticipation",
        ):
            self.assertIn(f"`{model_name}`", document)
        for projection_name in (
            "AttemptResult",
            "TrackProgress",
            "LeaderboardEntry",
            "ContentMetrics",
            "EngagementMetrics",
        ):
            self.assertIn(f"`{projection_name}`", document)
        for literal in (
            "RATING_POINTS",
            "STREAK_BONUS_STEP",
            "STREAK_BONUS_CAP",
            "attempt_registered(attempt, result)",
            "session_completed(enrollment, completed_at, idempotency_key)",
            "`title`",
            "`main`",
            "`content`",
            "`sidebar`",
            "`fragments`",
            "`scripts`",
            "`catalog`",
            "`learning`",
            "`gamification`",
            "`analytics`",
        ):
            self.assertIn(literal, document)

    def test_stub_docstrings_cover_the_complete_contract_policy(self):
        for module_name, function_name, _, state in SERVICE_CONTRACTS:
            if state != "STUB":
                continue
            function = getattr(importlib.import_module(module_name), function_name)
            docstring = inspect.getdoc(function) or ""
            for section in STUB_DOCSTRING_SECTIONS:
                with self.subTest(function=function_name, section=section):
                    self.assertIn(section, docstring)

    def test_documented_ownership_is_disjoint_and_complete(self):
        root = Path(__file__).resolve().parents[2]
        document = (root / "docs/contracts/domain-contracts.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(len(BASELINE_OWNERSHIP), 6)
        all_paths = []
        for feature, paths in BASELINE_OWNERSHIP.items():
            self.assertIn(feature, document)
            for path in paths:
                self.assertIn(f"`{path}`", document)
                all_paths.append(path)
        self.assertEqual(len(all_paths), len(set(all_paths)))

        self.assertEqual(len(BACKLOG_TRACES), 5)
        for backlog in BACKLOG_TRACES:
            self.assertIn(backlog, document)
        for migration_owner in (
            "`catalog/migrations/0002_domain_content.py`",
            "`learning/migrations/0001_initial.py`",
            "`gamification/migrations/0001_initial.py`",
        ):
            self.assertIn(migration_owner, document)
        self.assertIn(
            "gamification is the sole writer of `SeasonParticipation`", document
        )
        frozen_section = document.split("## Frozen Surfaces", 1)[1].split("##", 1)[0]
        self.assertNotIn("specs/004-domain-contracts/tasks.md", frozen_section)
