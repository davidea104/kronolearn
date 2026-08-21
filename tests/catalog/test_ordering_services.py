"""Atomic ordering behavior for tracks and modules."""

from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import CatalogChangeLog, CatalogState, Module, Track
from catalog.services.ordering import move_module, move_track


class TrackOrderingTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="admin@example.com",
            display_name="Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        self.tracks = [
            Track.objects.create(
                title=f"Track {position}",
                description="Descripcion",
                audience="Equipo",
                position=position,
            )
            for position in range(1, 4)
        ]

    def test_move_track_rewrites_consecutive_positions(self):
        outcome = move_track(
            self.actor,
            str(self.tracks[2].pk),
            position=1,
            expected_order_revision=0,
        )
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(
            list(Track.objects.values_list("title", "position")),
            [("Track 3", 1), ("Track 1", 2), ("Track 2", 3)],
        )
        self.assertEqual(CatalogState.objects.get().track_order_revision, 1)

    def test_move_track_rejects_invalid_position_and_stale_order(self):
        invalid = move_track(
            self.actor,
            str(self.tracks[0].pk),
            position=0,
            expected_order_revision=0,
        )
        stale = move_track(
            self.actor,
            str(self.tracks[0].pk),
            position=2,
            expected_order_revision=9,
        )
        self.assertEqual(invalid.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(stale.result, CatalogChangeLog.Result.CONFLICT)
        self.assertEqual(
            list(Track.objects.values_list("position", flat=True)), [1, 2, 3]
        )

    def test_move_track_supports_last_position_and_increments_changed_revisions(self):
        outcome = move_track(
            self.actor,
            str(self.tracks[0].pk),
            position=3,
            expected_order_revision=0,
        )
        self.assertTrue(outcome.changed)
        self.assertEqual(
            list(Track.objects.values_list("title", "position", "revision")),
            [("Track 2", 1, 2), ("Track 3", 2, 2), ("Track 1", 3, 2)],
        )

    def test_move_track_current_position_is_noop_and_audited(self):
        outcome = move_track(
            self.actor,
            str(self.tracks[1].pk),
            position=2,
            expected_order_revision=0,
        )
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertFalse(outcome.changed)
        self.assertEqual(CatalogState.objects.get().track_order_revision, 0)
        self.assertEqual(CatalogChangeLog.objects.count(), 1)

    def test_move_track_rolls_back_offset_and_audit_when_write_fails(self):
        original_positions = list(Track.objects.values_list("pk", "position"))
        with (
            patch.object(Track, "save", side_effect=RuntimeError("write failed")),
            self.assertRaises(RuntimeError),
        ):
            move_track(
                self.actor,
                str(self.tracks[2].pk),
                position=1,
                expected_order_revision=0,
            )
        self.assertEqual(
            list(Track.objects.values_list("pk", "position")),
            original_positions,
        )
        self.assertEqual(CatalogState.objects.get().track_order_revision, 0)
        self.assertFalse(CatalogChangeLog.objects.exists())

    def test_move_track_missing_reference_is_audited(self):
        outcome = move_track(
            self.actor,
            "not-a-track",
            position=1,
            expected_order_revision=0,
        )
        log = CatalogChangeLog.objects.get()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertIsNone(log.entity_id)
        self.assertEqual(len(log.unresolved_reference_digest), 64)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks required")
class TrackOrderingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        CatalogState.objects.get_or_create(pk=1, defaults={"track_order_revision": 0})
        self.actor = Account.objects.create_user(
            email="ordering@example.com",
            display_name="Ordering Admin",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.actor.groups.add(content_group)
        self.tracks = [
            Track.objects.create(
                title=f"Track {position}",
                description="Descripcion",
                audience="Equipo",
                position=position,
            )
            for position in range(1, 4)
        ]

    def _move_track(self, track):
        close_old_connections()
        try:
            return move_track(
                self.actor,
                str(track.pk),
                position=1,
                expected_order_revision=0,
            )
        finally:
            close_old_connections()

    def test_concurrent_moves_serialize_on_order_revision(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(self._move_track, self.tracks[1:]))
        self.assertCountEqual(
            [outcome.result for outcome in outcomes],
            [CatalogChangeLog.Result.SUCCESS, CatalogChangeLog.Result.CONFLICT],
        )
        self.assertEqual(
            list(Track.objects.order_by("position").values_list("position", flat=True)),
            [1, 2, 3],
        )
        self.assertEqual(CatalogState.objects.get().track_order_revision, 1)
        self.assertEqual(CatalogChangeLog.objects.count(), 2)


class ModuleOrderingTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="module-order@example.com",
            display_name="Module Ordering Admin",
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
        self.other_track = Track.objects.create(
            title="Otra",
            description="Descripcion",
            audience="Equipo",
            position=2,
        )
        self.modules = [
            Module.objects.create(
                track=self.track,
                title=f"Modulo {position}",
                objective="Objetivo",
                position=position,
            )
            for position in range(1, 4)
        ]

    def test_move_module_reorders_only_requested_track(self):
        other = Module.objects.create(
            track=self.other_track,
            title="Otro",
            objective="Objetivo",
            position=1,
        )
        outcome = move_module(
            self.actor,
            str(self.track.pk),
            str(self.modules[2].pk),
            position=1,
            expected_order_revision=0,
        )
        self.track.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(outcome.result, CatalogChangeLog.Result.SUCCESS)
        self.assertEqual(
            list(
                Module.objects.filter(track=self.track).values_list("title", "position")
            ),
            [("Modulo 3", 1), ("Modulo 1", 2), ("Modulo 2", 3)],
        )
        self.assertEqual(self.track.module_order_revision, 1)
        self.assertEqual(other.position, 1)

    def test_move_module_rejects_stale_invalid_and_parent_mismatch(self):
        invalid = move_module(
            self.actor,
            str(self.track.pk),
            str(self.modules[0].pk),
            position=0,
            expected_order_revision=0,
        )
        stale = move_module(
            self.actor,
            str(self.track.pk),
            str(self.modules[0].pk),
            position=2,
            expected_order_revision=4,
        )
        mismatch = move_module(
            self.actor,
            str(self.other_track.pk),
            str(self.modules[0].pk),
            position=1,
            expected_order_revision=0,
        )
        self.assertEqual(invalid.result, CatalogChangeLog.Result.INVALID)
        self.assertEqual(stale.result, CatalogChangeLog.Result.CONFLICT)
        self.assertEqual(mismatch.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(
            list(
                Module.objects.filter(track=self.track).values_list(
                    "position", flat=True
                )
            ),
            [1, 2, 3],
        )

    def test_move_module_rolls_back_offset_when_write_fails(self):
        original_positions = list(
            Module.objects.filter(track=self.track).values_list("pk", "position")
        )
        with (
            patch.object(Module, "save", side_effect=RuntimeError("write failed")),
            self.assertRaises(RuntimeError),
        ):
            move_module(
                self.actor,
                str(self.track.pk),
                str(self.modules[2].pk),
                position=1,
                expected_order_revision=0,
            )
        self.assertEqual(
            list(Module.objects.filter(track=self.track).values_list("pk", "position")),
            original_positions,
        )
        self.track.refresh_from_db()
        self.assertEqual(self.track.module_order_revision, 0)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks required")
class ModuleOrderingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        CatalogState.objects.get_or_create(pk=1, defaults={"track_order_revision": 0})
        self.actor = Account.objects.create_user(
            email="module-order-race@example.com",
            display_name="Module Order Race Admin",
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
        self.modules = [
            Module.objects.create(
                track=self.track,
                title=f"Modulo {position}",
                objective="Objetivo",
                position=position,
            )
            for position in range(1, 4)
        ]

    def _move_module(self, module):
        close_old_connections()
        try:
            return move_module(
                self.actor,
                str(self.track.pk),
                str(module.pk),
                position=1,
                expected_order_revision=0,
            )
        finally:
            close_old_connections()

    def test_concurrent_module_moves_serialize_on_parent_revision(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(self._move_module, self.modules[1:]))
        self.assertCountEqual(
            [outcome.result for outcome in outcomes],
            [CatalogChangeLog.Result.SUCCESS, CatalogChangeLog.Result.CONFLICT],
        )
        self.assertEqual(
            list(
                Module.objects.filter(track=self.track)
                .order_by("position")
                .values_list("position", flat=True)
            ),
            [1, 2, 3],
        )
        self.track.refresh_from_db()
        self.assertEqual(self.track.module_order_revision, 1)
        self.assertEqual(CatalogChangeLog.objects.count(), 2)
