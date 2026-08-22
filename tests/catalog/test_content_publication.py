"""Behavioral tests for creating and publishing learning content."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import Choice, ContentItem, ContentVersion, LabExercise
from catalog.services import content as content_service
from tests.factories.accounts import account_factory
from tests.factories.catalog import module_factory, track_factory


class ContentPublicationTests(TestCase):
    def setUp(self):
        content_admin_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor = account_factory(email="publication-admin@example.invalid")
        self.actor.groups.add(content_admin_group)
        self.track = track_factory(title="Publication Track", position=301)
        self.module = module_factory(
            track=self.track,
            title="Publication Module",
            status="INACTIVE",
            published_version=0,
        )

    def publication_payload(self):
        return {
            "expected_revision": 1,
            "title": "Unidad publicada",
            "learning_objective": "Tomar una decisión verificable",
            "lesson_text": "Una microlección completa y ficticia.",
            "case_prompt": "Un equipo ficticio debe elegir una alternativa.",
            "source": "KronoLearn curriculum test/publication/01",
            "reviewed_on": timezone.localdate(),
            "choices": (
                {
                    "position": 1,
                    "text": "Alternativa óptima",
                    "rating": Choice.Rating.OPTIMAL,
                    "consequence": "Produce evidencia.",
                    "explanation": "Cumple el objetivo.",
                },
                {
                    "position": 2,
                    "text": "Alternativa parcial",
                    "rating": Choice.Rating.PARTIAL,
                    "consequence": "Produce evidencia incompleta.",
                    "explanation": "Solo cubre parte del objetivo.",
                },
                {
                    "position": 3,
                    "text": "Alternativa incorrecta",
                    "rating": Choice.Rating.INCORRECT,
                    "consequence": "No produce evidencia.",
                    "explanation": "No cumple el objetivo.",
                },
            ),
            "lab": {
                "objective": "Aplicar la decisión",
                "initial_prompt": "Construye una evidencia pequeña.",
                "expected_artifact": "Un archivo verificable.",
                "verification_checklist": ("Ejecuta la comprobación",),
            },
        }

    def test_create_content_draft_appends_consecutive_positions(self):
        first = content_service.create_content_draft(
            self.module,
            self.actor,
            {"expected_revision": 1},
        )
        second = content_service.create_content_draft(
            self.module,
            self.actor,
            {"expected_revision": 2},
        )

        self.module.refresh_from_db()
        self.assertEqual([first.position, second.position], [1, 2])
        self.assertEqual([first.status, second.status], ["DRAFT", "DRAFT"])
        self.assertEqual(self.module.revision, 3)

    def test_publish_content_item_creates_complete_published_snapshot(self):
        item = ContentItem.objects.create(module=self.module, position=1)

        version = content_service.publish_content_item(
            item,
            self.actor,
            self.publication_payload(),
        )

        item.refresh_from_db()
        self.assertEqual(version.author, self.actor)
        self.assertEqual(
            version.editorial_status,
            ContentVersion.EditorialStatus.PUBLISHED,
        )
        self.assertEqual(
            list(version.choices.values_list("position", "rating")),
            [(1, "OPTIMAL"), (2, "PARTIAL"), (3, "INCORRECT")],
        )
        self.assertEqual(version.lab_exercise.objective, "Aplicar la decisión")
        self.assertEqual(item.status, ContentItem.Status.PUBLISHED)
        self.assertEqual(item.published_version, 1)
        self.assertEqual(item.revision, 2)

    def test_publish_content_item_rolls_back_when_a_component_fails(self):
        item = ContentItem.objects.create(module=self.module, position=1)

        with (
            patch.object(
                LabExercise.objects,
                "create",
                side_effect=IntegrityError("injected failure"),
            ),
            self.assertRaises(content_service.ContentRevisionConflict),
        ):
            content_service.publish_content_item(
                item,
                self.actor,
                self.publication_payload(),
            )

        item.refresh_from_db()
        self.assertEqual(ContentVersion.objects.count(), 0)
        self.assertEqual(item.status, ContentItem.Status.DRAFT)
        self.assertEqual(item.published_version, 0)
        self.assertEqual(item.revision, 1)

    def test_publish_content_item_rejects_invalid_payload_matrix(self):
        def five_choices(payload):
            fifth = dict(payload["choices"][0], position=5, text="Quinta opción")
            payload["choices"] += (fifth,)

        def duplicate_choice(payload):
            payload["choices"][1]["text"] = payload["choices"][0]["text"].upper()

        def broken_positions(payload):
            payload["choices"][1]["position"] = 3
            payload["choices"][2]["position"] = 4

        def no_optimal_choice(payload):
            for choice in payload["choices"]:
                choice["rating"] = Choice.Rating.PARTIAL

        cases = (
            ("invalid revision", lambda value: value.update(expected_revision=0)),
            ("stale revision", lambda value: value.update(expected_revision=2)),
            ("blank title", lambda value: value.update(title=" ")),
            (
                "long title",
                lambda value: value.update(title="x" * 161),
            ),
            (
                "blank learning objective",
                lambda value: value.update(learning_objective=" "),
            ),
            (
                "long learning objective",
                lambda value: value.update(learning_objective="x" * 1001),
            ),
            ("blank lesson", lambda value: value.update(lesson_text=" ")),
            ("blank case", lambda value: value.update(case_prompt=" ")),
            ("blank source", lambda value: value.update(source=" ")),
            ("long source", lambda value: value.update(source="x" * 501)),
            ("missing date", lambda value: value.update(reviewed_on=None)),
            (
                "future date",
                lambda value: value.update(
                    reviewed_on=timezone.localdate() + timedelta(days=1)
                ),
            ),
            (
                "two choices",
                lambda value: value.update(choices=value["choices"][:2]),
            ),
            ("five choices", five_choices),
            ("duplicate choice", duplicate_choice),
            ("broken positions", broken_positions),
            (
                "invalid rating",
                lambda value: value["choices"][0].update(rating="UNKNOWN"),
            ),
            ("no optimal choice", no_optimal_choice),
            (
                "blank choice text",
                lambda value: value["choices"][0].update(text=" "),
            ),
            (
                "blank consequence",
                lambda value: value["choices"][0].update(consequence=" "),
            ),
            (
                "blank explanation",
                lambda value: value["choices"][0].update(explanation=" "),
            ),
            (
                "blank lab objective",
                lambda value: value["lab"].update(objective=" "),
            ),
            (
                "blank lab prompt",
                lambda value: value["lab"].update(initial_prompt=" "),
            ),
            (
                "blank lab artifact",
                lambda value: value["lab"].update(expected_artifact=" "),
            ),
            (
                "empty lab checklist",
                lambda value: value["lab"].update(verification_checklist=()),
            ),
            (
                "blank lab checklist entry",
                lambda value: value["lab"].update(verification_checklist=(" ",)),
            ),
        )

        for position, (name, mutate) in enumerate(cases, start=1):
            with self.subTest(name=name):
                item = ContentItem.objects.create(
                    module=self.module,
                    position=position,
                )
                payload = deepcopy(self.publication_payload())
                mutate(payload)
                expected_error = (
                    content_service.ContentRevisionConflict
                    if name == "stale revision"
                    else ValidationError
                )

                with self.assertRaises(expected_error):
                    content_service.publish_content_item(
                        item,
                        self.actor,
                        payload,
                    )

                item.refresh_from_db()
                self.assertFalse(item.versions.exists())
                self.assertEqual(item.status, ContentItem.Status.DRAFT)
                self.assertEqual(item.published_version, 0)
                self.assertEqual(item.revision, 1)

    def test_publish_content_item_rejects_unauthorized_actor_without_writes(self):
        outsider = account_factory(email="publication-outsider@example.invalid")
        item = ContentItem.objects.create(module=self.module, position=1)

        with self.assertRaises(PermissionDenied):
            content_service.publish_content_item(
                item,
                outsider,
                self.publication_payload(),
            )

        item.refresh_from_db()
        self.assertFalse(item.versions.exists())
        self.assertEqual(item.status, ContentItem.Status.DRAFT)
        self.assertEqual(item.revision, 1)

    def test_correction_creates_next_version_and_preserves_previous_snapshot(self):
        item = ContentItem.objects.create(module=self.module, position=1)
        first = content_service.publish_content_item(
            item,
            self.actor,
            self.publication_payload(),
        )
        first_snapshot = (
            first.author_id,
            first.source,
            first.reviewed_on,
            first.published_at,
            tuple(
                first.choices.order_by("position").values_list(
                    "text", "rating", "consequence", "explanation"
                )
            ),
            first.lab_exercise.objective,
        )
        correction = self.publication_payload()
        correction.update(
            expected_revision=2,
            title="Unidad publicada corregida",
            source="KronoLearn curriculum test/publication/01 revision-2",
        )

        second = content_service.publish_content_item(
            item,
            self.actor,
            correction,
        )

        item.refresh_from_db()
        first.refresh_from_db()
        self.assertEqual((first.version_number, second.version_number), (1, 2))
        self.assertEqual(item.published_version, 2)
        self.assertEqual(item.revision, 3)
        self.assertEqual(
            (
                first.author_id,
                first.source,
                first.reviewed_on,
                first.published_at,
                tuple(
                    first.choices.order_by("position").values_list(
                        "text", "rating", "consequence", "explanation"
                    )
                ),
                first.lab_exercise.objective,
            ),
            first_snapshot,
        )
        self.assertEqual(second.author, self.actor)
        self.assertEqual(
            second.editorial_status,
            ContentVersion.EditorialStatus.PUBLISHED,
        )

    def test_published_version_components_reject_mutation_and_deletion(self):
        item = ContentItem.objects.create(module=self.module, position=1)
        version = content_service.publish_content_item(
            item,
            self.actor,
            self.publication_payload(),
        )
        choice = version.choices.get(position=1)
        lab = version.lab_exercise

        version.title = "Alterada"
        choice.text = "Alterada"
        lab.objective = "Alterado"
        for component in (version, choice, lab):
            with (
                self.subTest(component=type(component).__name__, operation="save"),
                self.assertRaises(ValidationError),
            ):
                component.save()
            with (
                self.subTest(component=type(component).__name__, operation="delete"),
                self.assertRaises(ValidationError),
            ):
                component.delete()

        version.refresh_from_db()
        choice.refresh_from_db()
        lab.refresh_from_db()
        self.assertEqual(version.title, "Unidad publicada")
        self.assertEqual(choice.text, "Alternativa óptima")
        self.assertEqual(lab.objective, "Aplicar la decisión")


@skipUnless(
    connection.vendor == "postgresql" and connection.features.has_select_for_update,
    "PostgreSQL row locks are required for concurrency tests.",
)
class ContentPublicationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        content_admin_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor = account_factory(email="publisher-race@example.invalid")
        self.actor.groups.add(content_admin_group)
        track = track_factory(title="Publication Race Track", position=302)
        self.module = module_factory(
            track=track,
            title="Publication Race Module",
            status="INACTIVE",
            published_version=0,
        )
        self.item = ContentItem.objects.create(module=self.module, position=1)

    def payload(self):
        return {
            "expected_revision": 1,
            "title": "Unidad concurrente",
            "learning_objective": "Publicar una sola versión",
            "lesson_text": "Una microlección ficticia.",
            "case_prompt": "Un equipo ficticio publica simultáneamente.",
            "source": "KronoLearn curriculum test/concurrency/01",
            "reviewed_on": timezone.localdate(),
            "choices": (
                {
                    "position": 1,
                    "text": "Opción óptima",
                    "rating": Choice.Rating.OPTIMAL,
                    "consequence": "Publicación consistente.",
                    "explanation": "Respeta la revisión bloqueada.",
                },
                {
                    "position": 2,
                    "text": "Opción parcial",
                    "rating": Choice.Rating.PARTIAL,
                    "consequence": "Resultado parcial.",
                    "explanation": "No cubre todo el objetivo.",
                },
                {
                    "position": 3,
                    "text": "Opción incorrecta",
                    "rating": Choice.Rating.INCORRECT,
                    "consequence": "Conflicto no controlado.",
                    "explanation": "Ignora la revisión.",
                },
            ),
            "lab": None,
        }

    def test_simultaneous_publications_accept_one_revision(self):
        barrier = Barrier(2)

        def publish():
            close_old_connections()
            try:
                barrier.wait()
                try:
                    return content_service.publish_content_item(
                        self.item,
                        self.actor,
                        self.payload(),
                    )
                except content_service.ContentRevisionConflict as exc:
                    return exc
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(executor.map(lambda _: publish(), range(2)))

        self.assertEqual(
            sum(isinstance(result, ContentVersion) for result in results), 1
        )
        self.assertEqual(
            sum(
                isinstance(result, content_service.ContentRevisionConflict)
                for result in results
            ),
            1,
        )
        self.item.refresh_from_db()
        self.assertEqual((self.item.revision, self.item.published_version), (2, 1))
        self.assertEqual(self.item.versions.count(), 1)
