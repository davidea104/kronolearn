"""Integration tests for deterministic learning-content reconciliation."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase

from accounts.security import CONTENT_ADMIN_ROLE
from catalog.content_data import load_definitions
from catalog.models import (
    CatalogChangeLog,
    CatalogState,
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
)
from catalog.services import content as content_service
from tests.factories.accounts import account_factory


class LearningContentLoadTests(TestCase):
    def setUp(self):
        content_admin_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor = account_factory(email="loader-admin@example.invalid")
        self.actor.groups.add(content_admin_group)
        self.definitions = load_definitions()

    def seed_legacy_graph(self, *, secondary_alias=False):
        legacy_items = []
        for track_position, definition in enumerate(self.definitions, start=1):
            title = (
                definition.legacy_titles[0]
                if secondary_alias and definition.legacy_titles
                else definition.title
            )
            track = Track.objects.create(
                title=title,
                description=definition.description,
                audience=definition.audience,
                position=track_position,
                status=Track.Status.ACTIVE,
                published_version=1,
            )
            TrackVersion.objects.create(
                track=track,
                version_number=1,
                title=title,
                description=definition.description,
                audience=definition.audience,
                author=self.actor,
                source="KronoLearn demo",
                reviewed_on=definition.reviewed_on,
                editorial_status=TrackVersion.EditorialStatus.APPROVED,
            )
            module = Module.objects.create(
                track=track,
                title=definition.module.title,
                objective=definition.module.objective,
                position=1,
                status=Module.Status.ACTIVE,
                published_version=1,
            )
            ModuleVersion.objects.create(
                module=module,
                version_number=1,
                title=definition.module.title,
                objective=definition.module.objective,
                author=self.actor,
                source="KronoLearn demo",
                reviewed_on=definition.module.reviewed_on,
                editorial_status=ModuleVersion.EditorialStatus.APPROVED,
            )
            item = ContentItem.objects.create(
                module=module,
                position=1,
                status=ContentItem.Status.PUBLISHED,
                published_version=1,
            )
            fingerprint = definition.module.units[0].legacy_fingerprint
            self.assertIsNotNone(fingerprint)
            version = ContentVersion.objects.create(
                content_item=item,
                version_number=1,
                title=fingerprint.title,
                learning_objective=fingerprint.learning_objective,
                lesson_text=fingerprint.lesson_text,
                case_prompt=fingerprint.case_prompt,
                source=fingerprint.source,
                author=self.actor,
                reviewed_on=definition.module.units[0].reviewed_on,
            )
            Choice.objects.bulk_create(
                [
                    Choice(
                        content_version=version,
                        position=choice.position,
                        text=choice.text,
                        rating=choice.rating,
                        consequence=choice.consequence,
                        explanation=choice.explanation,
                    )
                    for choice in fingerprint.choices
                ]
            )
            if fingerprint.lab is not None:
                LabExercise.objects.create(
                    content_version=version,
                    objective=fingerprint.lab.objective,
                    initial_prompt=fingerprint.lab.initial_prompt,
                    expected_artifact=fingerprint.lab.expected_artifact,
                    verification_checklist=list(fingerprint.lab.verification_checklist),
                )
            legacy_items.append(item)
        return tuple(legacy_items)

    def test_empty_database_load_publishes_complete_ordered_catalog(self):
        outcome = content_service.load_learning_content(
            str(self.actor.pk), self.definitions
        )

        self.assertTrue(outcome.changed)
        self.assertEqual(
            (
                outcome.track_count,
                outcome.module_count,
                outcome.content_item_count,
                outcome.items_created,
                outcome.versions_created,
            ),
            (2, 2, 10, 10, 10),
        )
        tracks = list(Track.objects.prefetch_related("modules__content_items"))
        self.assertEqual(
            [track.title for track in tracks],
            [
                "Crea tu registro de gastos con agentes y SDD",
                "Fundamentos de negocio para equipos técnicos",
            ],
        )
        self.assertEqual([track.status for track in tracks], ["ACTIVE", "ACTIVE"])
        self.assertEqual(
            [
                list(
                    track.modules.get().content_items.values_list("position", flat=True)
                )
                for track in tracks
            ],
            [list(range(1, 8)), list(range(1, 4))],
        )
        self.assertEqual(
            ContentItem.objects.filter(status=ContentItem.Status.PUBLISHED).count(),
            10,
        )
        self.assertEqual(
            ContentVersion.objects.filter(
                editorial_status=ContentVersion.EditorialStatus.PUBLISHED
            ).count(),
            10,
        )

        identities_before = tuple(
            ContentVersion.objects.order_by(
                "content_item__module__track__position",
                "content_item__position",
            ).values_list(
                "content_item_id",
                "id",
                "version_number",
                "published_at",
                "content_item__revision",
            )
        )
        repeated = content_service.load_learning_content(
            str(self.actor.pk), self.definitions
        )
        identities_after = tuple(
            ContentVersion.objects.order_by(
                "content_item__module__track__position",
                "content_item__position",
            ).values_list(
                "content_item_id",
                "id",
                "version_number",
                "published_at",
                "content_item__revision",
            )
        )

        self.assertFalse(repeated.changed)
        self.assertEqual((repeated.items_created, repeated.versions_created), (0, 0))
        self.assertEqual(identities_after, identities_before)

    def test_legacy_alias_and_position_one_units_converge_without_duplication(self):
        legacy_items = self.seed_legacy_graph(secondary_alias=True)
        legacy_ids = tuple(item.pk for item in legacy_items)

        outcome = content_service.load_learning_content(
            str(self.actor.pk), self.definitions
        )

        self.assertEqual(Track.objects.count(), 2)
        self.assertFalse(
            Track.objects.filter(
                title="Fundamentos de negocio para equipos tecnicos"
            ).exists()
        )
        self.assertTrue(
            Track.objects.filter(
                title="Fundamentos de negocio para equipos técnicos"
            ).exists()
        )
        current_position_one = tuple(
            ContentItem.objects.filter(position=1)
            .order_by("module__track__position")
            .values_list("pk", flat=True)
        )
        self.assertEqual(current_position_one, legacy_ids)
        self.assertEqual(
            list(
                ContentItem.objects.filter(position=1)
                .order_by("module__track__position")
                .values_list("published_version", flat=True)
            ),
            [2, 2],
        )
        self.assertEqual(ContentItem.objects.count(), 10)
        self.assertEqual(ContentVersion.objects.count(), 12)
        self.assertEqual((outcome.items_created, outcome.versions_created), (8, 10))

    def test_failure_during_publication_rolls_back_the_whole_load(self):
        real_publish = content_service.publish_content_item
        publication_count = 0

        def fail_on_second_publication(*args, **kwargs):
            nonlocal publication_count
            publication_count += 1
            if publication_count == 2:
                raise RuntimeError("injected publication failure")
            return real_publish(*args, **kwargs)

        with (
            patch.object(
                content_service,
                "publish_content_item",
                side_effect=fail_on_second_publication,
            ),
            self.assertRaisesRegex(RuntimeError, "injected publication failure"),
        ):
            content_service.load_learning_content(str(self.actor.pk), self.definitions)

        self.assertEqual(
            [
                model.objects.count()
                for model in (
                    Track,
                    TrackVersion,
                    Module,
                    ModuleVersion,
                    ContentItem,
                    ContentVersion,
                    Choice,
                    LabExercise,
                    CatalogChangeLog,
                )
            ],
            [0] * 9,
        )

    def target_module(self):
        definition = self.definitions[0]
        track = Track.objects.create(
            title=definition.title,
            description=definition.description,
            audience=definition.audience,
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title=definition.module.title,
            objective=definition.module.objective,
            position=1,
        )
        return track, module

    def assert_load_conflict_preserves_item(self, track, module, item):
        before = (track.pk, module.pk, item.pk, track.revision, module.revision)
        item_count = ContentItem.objects.count()

        with self.assertRaises(content_service.ContentLoadConflict):
            content_service.load_learning_content(str(self.actor.pk), self.definitions)

        track.refresh_from_db()
        module.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(
            (track.pk, module.pk, item.pk, track.revision, module.revision),
            before,
        )
        self.assertEqual((Track.objects.count(), Module.objects.count()), (1, 1))
        self.assertEqual(ContentItem.objects.count(), item_count)

    def test_foreign_expected_position_rejects_load_without_mutation(self):
        track, module = self.target_module()
        item = ContentItem.objects.create(
            module=module,
            position=1,
            status=ContentItem.Status.PUBLISHED,
            published_version=1,
        )
        ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Contenido ajeno",
            learning_objective="Objetivo ajeno",
            lesson_text="Lección ajena",
            case_prompt="Caso ajeno",
            source="Editorial externa",
            author=self.actor,
            reviewed_on=self.definitions[0].reviewed_on,
        )

        self.assert_load_conflict_preserves_item(track, module, item)

    def test_extra_position_rejects_load_without_mutation(self):
        track, module = self.target_module()
        for position in range(1, 8):
            ContentItem.objects.create(module=module, position=position)
        item = ContentItem.objects.create(module=module, position=8)

        self.assert_load_conflict_preserves_item(track, module, item)

    def test_gap_in_existing_positions_rejects_load_without_mutation(self):
        _, module = self.target_module()
        ContentItem.objects.create(module=module, position=1)
        ContentItem.objects.create(module=module, position=3)

        with self.assertRaises(content_service.ContentLoadConflict):
            content_service.load_learning_content(str(self.actor.pk), self.definitions)

        self.assertEqual(
            list(module.content_items.values_list("position", flat=True)), [1, 3]
        )
        self.assertEqual(ContentVersion.objects.count(), 0)

    def test_learner_read_returns_only_current_complete_versions_in_order(self):
        content_service.load_learning_content(str(self.actor.pk), self.definitions)
        tracks = tuple(Track.objects.order_by("position"))
        first_item = ContentItem.objects.get(
            module__track=tracks[0],
            position=1,
        )
        historical = ContentVersion.objects.create(
            content_item=first_item,
            version_number=2,
            title="Versión histórica no vigente",
            learning_objective="No debe aparecer",
            lesson_text="Contenido histórico ficticio.",
            case_prompt="Caso histórico ficticio.",
            source="KronoLearn curriculum test/history",
            author=self.actor,
            reviewed_on=self.definitions[0].reviewed_on,
        )

        published_by_track = tuple(
            content_service.list_published_versions(track) for track in tracks
        )

        self.assertEqual([len(versions) for versions in published_by_track], [7, 3])
        self.assertNotIn(
            historical.pk,
            {version.pk for versions in published_by_track for version in versions},
        )
        self.assertEqual(
            [
                version.content_item.position
                for versions in published_by_track
                for version in versions
            ],
            [*range(1, 8), *range(1, 4)],
        )
        self.assertTrue(
            all(
                version.editorial_status == ContentVersion.EditorialStatus.PUBLISHED
                and version.title
                and version.lesson_text
                and version.case_prompt
                and 3 <= version.choices.count() <= 4
                and all(
                    choice.consequence and choice.explanation
                    for choice in version.choices.all()
                )
                for versions in published_by_track
                for version in versions
            )
        )
        self.assertEqual(
            [
                hasattr(version, "lab_exercise")
                for versions in published_by_track
                for version in versions
            ],
            [True] * 7 + [False] * 3,
        )


@skipUnless(
    connection.vendor == "postgresql" and connection.features.has_select_for_update,
    "PostgreSQL row locks are required for concurrency tests.",
)
class LearningContentConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        CatalogState.objects.get_or_create(pk=1, defaults={"track_order_revision": 0})
        content_admin_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor = account_factory(email="concurrency-admin@example.invalid")
        self.actor.groups.add(content_admin_group)
        self.definitions = load_definitions()

    @staticmethod
    def run_workers(worker):
        barrier = Barrier(2)

        def run_one():
            close_old_connections()
            try:
                barrier.wait()
                return worker()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return tuple(executor.map(lambda _: run_one(), range(2)))

    def test_simultaneous_loads_converge_without_duplicates(self):
        outcomes = self.run_workers(
            lambda: content_service.load_learning_content(
                str(self.actor.pk), self.definitions
            )
        )

        self.assertEqual(
            [
                (
                    outcome.track_count,
                    outcome.module_count,
                    outcome.content_item_count,
                )
                for outcome in outcomes
            ],
            [(2, 2, 10), (2, 2, 10)],
        )
        self.assertEqual(sum(outcome.items_created for outcome in outcomes), 10)
        self.assertEqual(sum(outcome.versions_created for outcome in outcomes), 10)
        self.assertEqual(Track.objects.count(), 2)
        self.assertEqual(Module.objects.count(), 2)
        self.assertEqual(ContentItem.objects.count(), 10)
        self.assertEqual(ContentVersion.objects.count(), 10)

    def test_simultaneous_drafts_accept_only_one_expected_revision(self):
        track = Track.objects.create(
            title="Concurrent Track",
            description="Concurrent description",
            audience="Concurrent audience",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Concurrent Module",
            objective="Concurrent objective",
            position=1,
        )

        def create_draft():
            try:
                return content_service.create_content_draft(
                    module,
                    self.actor,
                    {"expected_revision": 1},
                )
            except content_service.ContentRevisionConflict as exc:
                return exc

        results = self.run_workers(create_draft)

        self.assertEqual(sum(isinstance(result, ContentItem) for result in results), 1)
        self.assertEqual(
            sum(
                isinstance(result, content_service.ContentRevisionConflict)
                for result in results
            ),
            1,
        )
        module.refresh_from_db()
        self.assertEqual(module.revision, 2)
        self.assertEqual(
            list(module.content_items.values_list("position", flat=True)), [1]
        )

    def test_simultaneous_reconciliation_creates_one_corrected_version(self):
        content_service.load_learning_content(str(self.actor.pk), self.definitions)
        principal = self.definitions[0]
        first_unit = principal.module.units[0]
        revised_unit = replace(
            first_unit,
            title="Define el problema, usuario y alcance mínimo corregidos",
        )
        revised_module = replace(
            principal.module,
            units=(revised_unit, *principal.module.units[1:]),
        )
        revised_definitions = (
            replace(principal, module=revised_module),
            self.definitions[1],
        )

        outcomes = self.run_workers(
            lambda: content_service.load_learning_content(
                str(self.actor.pk), revised_definitions
            )
        )

        self.assertEqual(sum(outcome.versions_created for outcome in outcomes), 1)
        item = ContentItem.objects.get(
            module__track__position=1,
            position=1,
        )
        self.assertEqual(item.published_version, 2)
        self.assertEqual(item.versions.count(), 2)
        self.assertEqual(
            item.versions.get(version_number=2).title,
            "Define el problema, usuario y alcance mínimo corregidos",
        )
