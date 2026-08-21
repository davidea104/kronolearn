"""Catalog command outcomes and transactional content behavior."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import timedelta
from unittest import skipUnless

from django.contrib.auth.models import Group
from django.core.signing import salted_hmac
from django.db import close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import (
    CatalogChangeLog,
    CatalogState,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
)
from catalog.services.content import (
    CatalogCommandOutcome,
    change_module_status,
    change_track_status,
    create_module,
    create_track,
    edit_module,
    edit_track,
    record_catalog_outcome,
    resolve_catalog_target,
)


class CatalogOutcomeTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="content@example.com",
            display_name="Content Admin",
            password="Strong-test-password-123",
        )

    def test_outcome_is_immutable(self):
        outcome = CatalogCommandOutcome(
            result=CatalogChangeLog.Result.SUCCESS,
            changed=False,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            field_errors={"title": ("Required",)},
        )
        with self.assertRaises(FrozenInstanceError):
            outcome.changed = True
        with self.assertRaises(TypeError):
            outcome.field_errors["title"] = ("Changed",)

    def test_unresolved_reference_is_deterministic_and_never_stored_raw(self):
        first = record_catalog_outcome(
            actor=self.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference="not-a-uuid",
        )
        second = record_catalog_outcome(
            actor=self.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference="not-a-uuid",
        )
        logs = list(CatalogChangeLog.objects.order_by("occurred_at"))
        self.assertEqual(CatalogChangeLog.objects.count(), 2)
        self.assertEqual(
            logs[0].unresolved_reference_digest,
            logs[1].unresolved_reference_digest,
        )
        self.assertEqual(len(logs[0].unresolved_reference_digest), 64)
        self.assertNotIn("not-a-uuid", logs[0].unresolved_reference_digest)
        self.assertEqual(
            logs[0].unresolved_reference_digest,
            salted_hmac(
                "catalog.track.reference",
                "not-a-uuid",
                algorithm="sha256",
            ).hexdigest(),
        )
        self.assertEqual(first.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(second.result, CatalogChangeLog.Result.NOT_FOUND)

    def test_target_resolution_derives_authorization_from_locked_actor(self):
        track = Track.objects.create(
            title="Fundamentos",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        with transaction.atomic():
            denied = resolve_catalog_target(self.actor, Track, str(track.pk))
        self.assertFalse(denied.authorized)
        self.assertIsNone(denied.entity)
        self.assertEqual(denied.unresolved_reference, str(track.pk))

        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        with transaction.atomic():
            allowed = resolve_catalog_target(self.actor, Track, str(track.pk))
        self.assertTrue(allowed.authorized)
        self.assertEqual(allowed.entity, track)
        self.assertIsNone(allowed.unresolved_reference)


class TrackCommandTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="admin@example.com",
            display_name="Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)

    def test_create_track_normalizes_and_appends_atomically(self):
        outcome = create_track(
            self.actor,
            title="  Fundamentos  ",
            description=" Descripcion ",
            audience=" Equipo ",
        )
        track = Track.objects.get()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertTrue(outcome.changed)
        self.assertEqual((track.title, track.position), ("Fundamentos", 1))
        self.assertEqual(CatalogState.objects.get().track_order_revision, 1)
        self.assertEqual(CatalogChangeLog.objects.count(), 1)

    def test_create_track_denies_actor_without_role_without_mutation(self):
        outsider = Account.objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password="Strong-test-password-123",
        )
        outcome = create_track(
            outsider,
            title="Oculto",
            description="Descripcion",
            audience="Equipo",
        )
        self.assertEqual(outcome.result, CatalogChangeLog.Result.DENIED)
        self.assertFalse(outcome.changed)
        self.assertFalse(Track.objects.exists())
        self.assertEqual(CatalogChangeLog.objects.get().result, "DENIED")

    def test_create_track_rejects_blank_overlong_and_duplicate_normalized_title(self):
        blank = create_track(
            self.actor,
            title=" ",
            description="",
            audience="",
        )
        Track.objects.create(
            title="Fundamentos",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        duplicate = create_track(
            self.actor,
            title="  FUNDAMENTOS ",
            description="Descripcion",
            audience="Equipo",
        )
        overlong = create_track(
            self.actor,
            title="x" * 161,
            description="Descripcion",
            audience="Equipo",
        )
        self.assertEqual(blank.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(duplicate.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(overlong.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(CatalogChangeLog.objects.count(), 3)

    def test_edit_track_rejects_stale_revision(self):
        track = Track.objects.create(
            title="Inicial",
            description="Descripcion",
            audience="Equipo",
            position=1,
            revision=2,
        )
        outcome = edit_track(
            self.actor,
            str(track.pk),
            expected_revision=1,
            title="Obsoleto",
            description="Descripcion",
            audience="Equipo",
        )
        track.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.CONFLICT)
        self.assertEqual(track.title, "Inicial")

    def test_active_edit_publishes_but_inactive_edit_does_not(self):
        inactive = Track.objects.create(
            title="Inactivo",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        active = Track.objects.create(
            title="Activo",
            description="Descripcion",
            audience="Equipo",
            position=2,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        inactive_outcome = edit_track(
            self.actor,
            str(inactive.pk),
            expected_revision=1,
            title="Inactivo editado",
            description="Descripcion",
            audience="Equipo",
        )
        active_outcome = edit_track(
            self.actor,
            str(active.pk),
            expected_revision=1,
            title="Activo editado",
            description="Descripcion",
            audience="Equipo",
            publication={
                "source": "https://example.com/editorial",
                "reviewed_on": timezone.localdate(),
                "editorial_status": TrackVersion.EditorialStatus.APPROVED,
            },
        )
        active.refresh_from_db()
        self.assertEqual(inactive_outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertFalse(inactive.versions.exists())
        self.assertEqual(active_outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(active.published_version, 2)
        self.assertEqual(active.versions.get().source, "https://example.com/editorial")

    def test_active_edit_title_collision_rolls_back_snapshot(self):
        Track.objects.create(
            title="Reservado",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        active = Track.objects.create(
            title="Activo",
            description="Descripcion",
            audience="Equipo",
            position=2,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        outcome = edit_track(
            self.actor,
            str(active.pk),
            expected_revision=1,
            title=" RESERVADO ",
            description="Descripcion nueva",
            audience="Equipo",
            publication={
                "source": "DOC-002",
                "reviewed_on": timezone.localdate(),
                "editorial_status": TrackVersion.EditorialStatus.APPROVED,
            },
        )
        active.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual((active.title, active.published_version), ("Activo", 1))
        self.assertFalse(active.versions.exists())

    def test_active_edit_without_metadata_preserves_content_and_version(self):
        active = Track.objects.create(
            title="Activo",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )

        outcome = edit_track(
            self.actor,
            str(active.pk),
            expected_revision=1,
            title="Cambio rechazado",
            description="Descripcion nueva",
            audience="Otro equipo",
        )

        active.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(
            (
                active.title,
                active.description,
                active.audience,
                active.revision,
                active.published_version,
            ),
            ("Activo", "Descripcion", "Equipo", 1, 1),
        )
        self.assertFalse(active.versions.exists())

    def test_activation_reactivation_and_current_noop_version_correctly(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        metadata = {
            "source": " DOC-001 ",
            "reviewed_on": timezone.localdate(),
            "editorial_status": TrackVersion.EditorialStatus.APPROVED,
        }
        activated = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=1,
            target_status=Track.Status.ACTIVE,
            publication=metadata,
        )
        noop = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=2,
            target_status=Track.Status.ACTIVE,
            publication=metadata,
        )
        deactivated = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=2,
            target_status=Track.Status.INACTIVE,
        )
        reactivated = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=3,
            target_status=Track.Status.ACTIVE,
            publication={**metadata, "source": "DOC-002"},
        )
        track.refresh_from_db()
        self.assertTrue(activated.changed)
        self.assertFalse(noop.changed)
        self.assertTrue(deactivated.changed)
        self.assertTrue(reactivated.changed)
        self.assertEqual(track.published_version, 2)
        self.assertEqual(track.revision, 4)
        self.assertEqual(
            list(
                track.versions.order_by("version_number").values_list(
                    "version_number", "source"
                )
            ),
            [(1, "DOC-001"), (2, "DOC-002")],
        )

    def test_stale_state_request_conflicts_before_noop(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
            revision=2,
        )
        outcome = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=1,
            target_status=Track.Status.ACTIVE,
        )
        self.assertEqual(outcome.result, CatalogChangeLog.Result.CONFLICT)
        self.assertFalse(outcome.changed)
        self.assertFalse(track.versions.exists())

    def test_activation_validates_metadata_and_requires_active_module(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        Module.objects.create(
            track=track,
            title="Modulo inactivo",
            objective="Objetivo",
            position=1,
        )
        outcome = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=1,
            target_status=Track.Status.ACTIVE,
            publication={
                "source": " ",
                "reviewed_on": timezone.localdate() + timedelta(days=1),
                "editorial_status": "DRAFT",
            },
        )
        self.assertEqual(outcome.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(
            set(outcome.field_errors),
            {"source", "reviewed_on", "editorial_status", "status"},
        )
        self.assertEqual(CatalogChangeLog.objects.count(), 1)

    def test_publication_source_is_free_text_trimmed_and_bounded(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        valid = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=1,
            target_status=Track.Status.ACTIVE,
            publication={
                "source": "  Manual interno 42  ",
                "reviewed_on": timezone.localdate(),
                "editorial_status": TrackVersion.EditorialStatus.APPROVED,
            },
        )
        change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=2,
            target_status=Track.Status.INACTIVE,
        )
        overlong = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=3,
            target_status=Track.Status.ACTIVE,
            publication={
                "source": "x" * 501,
                "reviewed_on": timezone.localdate(),
                "editorial_status": TrackVersion.EditorialStatus.APPROVED,
            },
        )

        track.refresh_from_db()
        self.assertEqual(valid.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(track.versions.get().source, "Manual interno 42")
        self.assertEqual(overlong.result, CatalogChangeLog.Result.INVALID)
        self.assertIn("source", overlong.field_errors)
        self.assertEqual(track.status, Track.Status.INACTIVE)
        self.assertEqual(track.published_version, 1)

    def test_deactivating_track_preserves_module_states_and_positions(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        active = Module.objects.create(
            track=track,
            title="Activo",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        inactive = Module.objects.create(
            track=track,
            title="Inactivo",
            objective="Objetivo",
            position=2,
        )

        outcome = change_track_status(
            self.actor,
            str(track.pk),
            expected_revision=1,
            target_status=Track.Status.INACTIVE,
        )

        active.refresh_from_db()
        inactive.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(
            (active.status, active.position),
            (Module.Status.ACTIVE, 1),
        )
        self.assertEqual(
            (inactive.status, inactive.position),
            (Module.Status.INACTIVE, 2),
        )

    def test_missing_and_malformed_references_are_audited_without_raw_value(self):
        missing = edit_track(
            self.actor,
            "00000000-0000-0000-0000-000000000001",
            expected_revision=1,
            title="Track",
            description="Descripcion",
            audience="Equipo",
        )
        malformed = edit_track(
            self.actor,
            "private-reference",
            expected_revision=1,
            title="Track",
            description="Descripcion",
            audience="Equipo",
        )
        self.assertEqual(missing.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(malformed.result, CatalogChangeLog.Result.NOT_FOUND)
        for digest in CatalogChangeLog.objects.values_list(
            "unresolved_reference_digest", flat=True
        ):
            self.assertEqual(len(digest), 64)
            self.assertNotIn("private-reference", digest)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks required")
class TrackVersionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        CatalogState.objects.get_or_create(pk=1, defaults={"track_order_revision": 0})
        self.actor = Account.objects.create_user(
            email="concurrent@example.com",
            display_name="Concurrent Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        self.track = Track.objects.create(
            title="Concurrente",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )

    def _edit_active_track(self, title):
        close_old_connections()
        try:
            return edit_track(
                self.actor,
                str(self.track.pk),
                expected_revision=1,
                title=title,
                description="Descripcion",
                audience="Equipo",
                publication={
                    "source": title,
                    "reviewed_on": timezone.localdate(),
                    "editorial_status": TrackVersion.EditorialStatus.APPROVED,
                },
            )
        finally:
            close_old_connections()

    def test_concurrent_active_edits_publish_one_next_version(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(
                executor.map(self._edit_active_track, ("Edicion A", "Edicion B"))
            )
        self.track.refresh_from_db()
        self.assertCountEqual(
            [outcome.result for outcome in outcomes],
            [CatalogChangeLog.Result.SUCCESS, CatalogChangeLog.Result.CONFLICT],
        )
        self.assertEqual(self.track.published_version, 2)
        self.assertEqual(
            list(self.track.versions.values_list("version_number", flat=True)),
            [2],
        )
        self.assertEqual(CatalogChangeLog.objects.count(), 2)


class ModuleCommandTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="modules@example.com",
            display_name="Module Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        self.track = Track.objects.create(
            title="Ruta A",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.other_track = Track.objects.create(
            title="Ruta B",
            description="Descripcion",
            audience="Equipo",
            position=2,
        )
        self.metadata = {
            "source": "DOC-MOD-001",
            "reviewed_on": timezone.localdate(),
            "editorial_status": ModuleVersion.EditorialStatus.APPROVED,
        }

    def test_create_module_derives_parent_appends_and_scopes_title_uniqueness(self):
        created = create_module(
            self.actor,
            str(self.track.pk),
            title=" Introduccion ",
            objective=" Objetivo ",
        )
        duplicate = create_module(
            self.actor,
            str(self.track.pk),
            title="INTRODUCCION",
            objective="Otro",
        )
        other_parent = create_module(
            self.actor,
            str(self.other_track.pk),
            title="Introduccion",
            objective="Objetivo",
        )
        module = Module.objects.get(track=self.track)
        self.track.refresh_from_db()
        self.assertEqual(created.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(
            (module.title, module.objective, module.position),
            ("Introduccion", "Objetivo", 1),
        )
        self.assertEqual(duplicate.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(other_parent.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(self.track.module_order_revision, 1)
        self.assertEqual(CatalogChangeLog.objects.count(), 3)

    def test_module_edit_keeps_parent_position_and_versions_only_when_active(self):
        inactive = Module.objects.create(
            track=self.track,
            title="Inactivo",
            objective="Objetivo",
            position=1,
        )
        active = Module.objects.create(
            track=self.track,
            title="Activo",
            objective="Objetivo",
            position=2,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        edit_module(
            self.actor,
            str(self.track.pk),
            str(inactive.pk),
            expected_revision=1,
            title="Inactivo editado",
            objective="Nuevo objetivo",
        )
        outcome = edit_module(
            self.actor,
            str(self.track.pk),
            str(active.pk),
            expected_revision=1,
            title="Activo editado",
            objective="Nuevo objetivo",
            publication=self.metadata,
        )
        active.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual((active.track_id, active.position), (self.track.pk, 2))
        self.assertEqual(active.published_version, 2)
        self.assertEqual(active.versions.get().version_number, 2)
        self.assertFalse(inactive.versions.exists())

    def test_active_module_edit_without_metadata_preserves_content_and_version(self):
        active = Module.objects.create(
            track=self.track,
            title="Activo",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )

        outcome = edit_module(
            self.actor,
            str(self.track.pk),
            str(active.pk),
            expected_revision=1,
            title="Cambio rechazado",
            objective="Objetivo nuevo",
        )

        active.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(
            (
                active.title,
                active.objective,
                active.revision,
                active.published_version,
            ),
            ("Activo", "Objetivo", 1, 1),
        )
        self.assertFalse(active.versions.exists())

    def test_module_activation_reactivation_noop_and_stale_revision(self):
        module = Module.objects.create(
            track=self.track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        activated = change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=1,
            target_status=Module.Status.ACTIVE,
            publication=self.metadata,
        )
        stale_noop = change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=1,
            target_status=Module.Status.ACTIVE,
        )
        noop = change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=2,
            target_status=Module.Status.ACTIVE,
        )
        change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=2,
            target_status=Module.Status.INACTIVE,
        )
        reactivated = change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=3,
            target_status=Module.Status.ACTIVE,
            publication={**self.metadata, "source": "https://example.com/module"},
        )
        module.refresh_from_db()
        self.assertTrue(activated.changed)
        self.assertEqual(stale_noop.result, CatalogChangeLog.Result.CONFLICT)
        self.assertFalse(noop.changed)
        self.assertTrue(reactivated.changed)
        self.assertEqual((module.published_version, module.revision), (2, 4))
        self.assertEqual(
            list(
                module.versions.order_by("version_number").values_list(
                    "source", flat=True
                )
            ),
            ["DOC-MOD-001", "https://example.com/module"],
        )

    def test_last_active_module_of_active_track_cannot_be_deactivated(self):
        self.track.status = Track.Status.ACTIVE
        self.track.published_version = 1
        self.track.save()
        module = Module.objects.create(
            track=self.track,
            title="Unico",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        outcome = change_module_status(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=1,
            target_status=Module.Status.INACTIVE,
        )
        module.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(module.status, Module.Status.ACTIVE)

    def test_deactivating_module_with_replacement_preserves_positions(self):
        self.track.status = Track.Status.ACTIVE
        self.track.published_version = 1
        self.track.save()
        first = Module.objects.create(
            track=self.track,
            title="Primero",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        second = Module.objects.create(
            track=self.track,
            title="Segundo",
            objective="Objetivo",
            position=2,
            status=Module.Status.ACTIVE,
            published_version=1,
        )

        outcome = change_module_status(
            self.actor,
            str(self.track.pk),
            str(first.pk),
            expected_revision=1,
            target_status=Module.Status.INACTIVE,
        )

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual((first.status, first.position), (Module.Status.INACTIVE, 1))
        self.assertEqual((second.status, second.position), (Module.Status.ACTIVE, 2))

    def test_module_must_belong_to_requested_track_and_missing_parent_is_opaque(self):
        module = Module.objects.create(
            track=self.other_track,
            title="Ajeno",
            objective="Objetivo",
            position=1,
        )
        mismatch = edit_module(
            self.actor,
            str(self.track.pk),
            str(module.pk),
            expected_revision=1,
            title="No permitido",
            objective="Objetivo",
        )
        missing_parent = create_module(
            self.actor,
            "not-a-track",
            title="Modulo",
            objective="Objetivo",
        )
        self.assertEqual(mismatch.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(missing_parent.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(CatalogChangeLog.objects.count(), 2)
        self.assertTrue(
            all(
                len(digest) == 64
                for digest in CatalogChangeLog.objects.values_list(
                    "unresolved_reference_digest", flat=True
                )
            )
        )


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks required")
class ModuleVersionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        CatalogState.objects.get_or_create(pk=1, defaults={"track_order_revision": 0})
        self.actor = Account.objects.create_user(
            email="module-race@example.com",
            display_name="Module Race Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        self.track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.module = Module.objects.create(
            track=self.track,
            title="Concurrente",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )

    def _edit_active_module(self, title):
        close_old_connections()
        try:
            return edit_module(
                self.actor,
                str(self.track.pk),
                str(self.module.pk),
                expected_revision=1,
                title=title,
                objective="Objetivo",
                publication={
                    "source": title,
                    "reviewed_on": timezone.localdate(),
                    "editorial_status": ModuleVersion.EditorialStatus.APPROVED,
                },
            )
        finally:
            close_old_connections()

    def test_concurrent_active_module_edits_publish_one_next_version(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(
                executor.map(self._edit_active_module, ("Edicion A", "Edicion B"))
            )
        self.module.refresh_from_db()
        self.assertCountEqual(
            [outcome.result for outcome in outcomes],
            [CatalogChangeLog.Result.SUCCESS, CatalogChangeLog.Result.CONFLICT],
        )
        self.assertEqual(self.module.published_version, 2)
        self.assertEqual(self.module.versions.get().version_number, 2)
        self.assertEqual(CatalogChangeLog.objects.count(), 2)
