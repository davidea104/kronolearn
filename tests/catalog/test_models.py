"""Persistence invariants for catalog content, versions, and audit evidence."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import (
    CatalogChangeLog,
    CatalogState,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
)


class CatalogModelTests(TestCase):
    def setUp(self):
        self.author = Account.objects.create_user(
            email="author@example.com",
            display_name="Author",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="  Fundamentos  ",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )

    def test_track_normalizes_identity_and_uses_safe_defaults(self):
        self.assertEqual(self.track.title, "Fundamentos")
        self.assertEqual(self.track.title_key, "fundamentos")
        self.assertEqual(self.track.status, Track.Status.INACTIVE)
        self.assertEqual(self.track.revision, 1)
        self.assertEqual(self.track.module_order_revision, 0)
        self.assertEqual(self.track.published_version, 0)

    def test_track_title_and_position_are_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Track.objects.create(
                title="FUNDAMENTOS",
                description="Otra",
                audience="Otra",
                position=2,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Track.objects.create(
                title="Otro",
                description="Otra",
                audience="Otra",
                position=1,
            )

    def test_module_title_and_position_are_unique_only_within_track(self):
        module = Module.objects.create(
            track=self.track,
            title=" Introduccion ",
            objective="Comprender",
            position=1,
        )
        other_track = Track.objects.create(
            title="Practica",
            description="Descripcion",
            audience="Equipo",
            position=2,
        )
        Module.objects.create(
            track=other_track,
            title="INTRODUCCION",
            objective="Aplicar",
            position=1,
        )
        self.assertEqual(module.title_key, "introduccion")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Module.objects.create(
                track=self.track,
                title="INTRODUCCION",
                objective="Duplicado",
                position=2,
            )

    def test_active_content_requires_a_published_version(self):
        self.track.status = Track.Status.ACTIVE
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.track.save()

    def test_catalog_state_is_the_singleton_row(self):
        state = CatalogState.objects.get(id=1)
        self.assertEqual(state.track_order_revision, 0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CatalogState.objects.create(id=2)

    def test_versions_are_immutable_after_insert(self):
        track_version = TrackVersion.objects.create(
            track=self.track,
            version_number=1,
            title=self.track.title,
            description=self.track.description,
            audience=self.track.audience,
            author=self.author,
            source=" DOC-001 ",
            reviewed_on=timezone.localdate(),
            editorial_status=TrackVersion.EditorialStatus.APPROVED,
        )
        self.assertEqual(track_version.source, "DOC-001")
        track_version.title = "Alterado"
        with self.assertRaises(ValidationError):
            track_version.save()
        with self.assertRaises(ValidationError):
            track_version.delete()

    def test_audit_reference_fields_are_mutually_exclusive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CatalogChangeLog.objects.create(
                actor=self.author,
                action=CatalogChangeLog.Action.EDIT,
                entity_type=CatalogChangeLog.EntityType.TRACK,
                entity_id=self.track.pk,
                unresolved_reference_digest="a" * 64,
                result=CatalogChangeLog.Result.NOT_FOUND,
                changed=False,
            )

    def test_module_version_relationships_are_protected(self):
        module = Module.objects.create(
            track=self.track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        ModuleVersion.objects.create(
            module=module,
            version_number=1,
            title=module.title,
            objective=module.objective,
            author=self.author,
            source="https://example.com/source",
            reviewed_on=timezone.localdate(),
            editorial_status=ModuleVersion.EditorialStatus.APPROVED,
        )
        with self.assertRaises(ValidationError):
            module.versions.get().delete()
