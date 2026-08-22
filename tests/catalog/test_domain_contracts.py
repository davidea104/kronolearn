"""Contract tests for shared catalog content entities."""

import inspect
from dataclasses import FrozenInstanceError, fields

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import (
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    Track,
)
from catalog.services import content as content_service
from catalog.services.content import (
    create_content_draft,
    get_published_version,
    list_published_versions,
    publish_content_item,
)
from tests.factories.accounts import account_factory
from tests.factories.catalog import (
    choice_factory,
    content_item_factory,
    content_version_factory,
    lab_exercise_factory,
    module_factory,
    track_factory,
)


class CatalogDomainContractTests(TestCase):
    def setUp(self):
        self.author = Account.objects.create_user(
            email="domain-author@example.com",
            display_name="Domain Author",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="Track de prueba",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.module = Module.objects.create(
            track=self.track,
            title="Modulo de prueba",
            objective="Objetivo",
            position=1,
        )

    def test_content_item_enforces_position_and_published_version(self):
        ContentItem.objects.create(module=self.module, position=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContentItem.objects.create(module=self.module, position=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContentItem.objects.create(module=self.module, position=0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContentItem.objects.create(
                module=self.module,
                position=2,
                status=ContentItem.Status.PUBLISHED,
                published_version=0,
            )

    def test_content_snapshot_is_immutable_and_current_is_derived(self):
        item = ContentItem.objects.create(
            module=self.module,
            position=1,
            status=ContentItem.Status.PUBLISHED,
            published_version=1,
        )
        version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Version",
            learning_objective="Aprender",
            lesson_text="Leccion",
            case_prompt="Caso",
            source=" Fuente ",
            author=self.author,
            reviewed_on=timezone.localdate(),
        )
        choice = Choice.objects.create(
            content_version=version,
            text="Respuesta",
            position=1,
            rating=Choice.Rating.OPTIMAL,
            consequence="Consecuencia",
            explanation="Explicacion",
        )
        lab = LabExercise.objects.create(
            content_version=version,
            objective="Practicar",
            initial_prompt="Empieza",
            expected_artifact="Archivo",
            verification_checklist=["Ejecuta la prueba"],
        )

        self.assertTrue(version.is_current)
        self.assertEqual(version.source, "Fuente")
        for snapshot in (version, choice, lab):
            with self.assertRaises(ValidationError):
                snapshot.delete()

    def test_choice_position_is_bounded_per_version(self):
        item = ContentItem.objects.create(module=self.module, position=1)
        version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Version",
            learning_objective="Aprender",
            lesson_text="Leccion",
            case_prompt="Caso",
            source="Fuente",
            author=self.author,
            reviewed_on=timezone.localdate(),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Choice.objects.create(
                content_version=version,
                text="Fuera de rango",
                position=5,
                rating=Choice.Rating.INCORRECT,
                consequence="Consecuencia",
                explanation="Explicacion",
            )

    def test_content_service_signatures_are_stable(self):
        self.assertEqual(
            tuple(inspect.signature(publish_content_item).parameters),
            ("content_item", "actor", "payload"),
        )
        self.assertEqual(
            tuple(inspect.signature(create_content_draft).parameters),
            ("module", "actor", "payload"),
        )
        self.assertEqual(
            tuple(inspect.signature(get_published_version).parameters),
            ("content_item",),
        )
        self.assertEqual(
            tuple(inspect.signature(list_published_versions).parameters),
            ("track",),
        )
        self.assertEqual(
            tuple(inspect.signature(content_service.load_learning_content).parameters),
            ("actor_ref", "definitions"),
        )

    def test_content_load_contract_types_are_stable_and_immutable(self):
        self.assertTrue(issubclass(content_service.ContentRevisionConflict, Exception))
        self.assertTrue(issubclass(content_service.ContentLoadConflict, Exception))
        self.assertEqual(
            tuple(field.name for field in fields(content_service.ContentLoadOutcome)),
            (
                "changed",
                "track_count",
                "module_count",
                "content_item_count",
                "items_created",
                "versions_created",
            ),
        )
        outcome = content_service.ContentLoadOutcome(
            changed=False,
            track_count=2,
            module_count=2,
            content_item_count=10,
            items_created=0,
            versions_created=0,
        )
        with self.assertRaises(FrozenInstanceError):
            outcome.changed = True

    def test_published_version_queries_are_exact_and_deterministic(self):
        other_module = Module.objects.create(
            track=self.track,
            title="Modulo inicial",
            objective="Objetivo",
            position=2,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        self.module.status = Module.Status.ACTIVE
        self.module.published_version = 1
        self.module.save()
        later_item = ContentItem.objects.create(
            module=self.module,
            position=2,
            status=ContentItem.Status.PUBLISHED,
            published_version=2,
        )
        earlier_item = ContentItem.objects.create(
            module=self.module,
            position=1,
            status=ContentItem.Status.PUBLISHED,
            published_version=1,
        )
        ignored_item = ContentItem.objects.create(
            module=other_module,
            position=1,
            status=ContentItem.Status.DRAFT,
        )
        versions = [
            ContentVersion.objects.create(
                content_item=item,
                version_number=version_number,
                title=f"Version {version_number}",
                learning_objective="Aprender",
                lesson_text="Leccion",
                case_prompt="Caso",
                source="Fuente",
                author=self.author,
                reviewed_on=timezone.localdate(),
            )
            for item, version_number in (
                (later_item, 1),
                (later_item, 2),
                (earlier_item, 1),
                (ignored_item, 1),
            )
        ]

        self.assertEqual(get_published_version(later_item), versions[1])
        self.assertIsNone(get_published_version(ignored_item))
        self.assertEqual(
            list_published_versions(self.track), [versions[2], versions[1]]
        )

    def test_catalog_factories_create_valid_defaults_and_accept_overrides(self):
        account = account_factory(email="factory-author@example.invalid")
        track = track_factory(title="Factory Override Track", position=8)
        module = module_factory(track=track, title="Factory Override Module")
        item = content_item_factory(module=module, position=3)
        version = content_version_factory(
            content_item=item, author=account, title="Factory Override Version"
        )
        choice = choice_factory(content_version=version, rating=Choice.Rating.PARTIAL)
        lab = lab_exercise_factory(content_version=version)

        self.assertEqual(track.position, 8)
        self.assertEqual(module.track, track)
        self.assertEqual(item.module, module)
        self.assertEqual(version.author, account)
        self.assertEqual(choice.rating, Choice.Rating.PARTIAL)
        self.assertEqual(lab.content_version, version)
