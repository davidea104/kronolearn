"""Learner catalog query projections and visibility."""

from django.test import TestCase

from catalog.models import Module, Track
from catalog.services.queries import (
    get_active_module,
    get_active_track,
    list_active_tracks,
)


class LearnerCatalogQueryTests(TestCase):
    def setUp(self):
        self.active_track = Track.objects.create(
            title="Ruta activa",
            description="Descripcion",
            audience="Equipo",
            position=2,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        self.first_track = Track.objects.create(
            title="Ruta primera",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
        )
        self.inactive_track = Track.objects.create(
            title="Ruta oculta",
            description="Privado",
            audience="Equipo",
            position=3,
        )
        self.active_module = Module.objects.create(
            track=self.active_track,
            title="Modulo activo",
            objective="Objetivo",
            position=2,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        Module.objects.create(
            track=self.active_track,
            title="Modulo oculto",
            objective="Privado",
            position=1,
        )

    def test_list_active_tracks_is_ordered_projected_and_one_query(self):
        with self.assertNumQueries(1):
            tracks = list(list_active_tracks())
        self.assertEqual(
            [track.title for track in tracks], ["Ruta primera", "Ruta activa"]
        )
        self.assertTrue(
            {
                "title_key",
                "status",
                "revision",
                "module_order_revision",
                "published_version",
            }
            <= tracks[0].get_deferred_fields()
        )

    def test_active_track_prefetches_only_active_modules_in_two_queries(self):
        with self.assertNumQueries(2):
            track = get_active_track(self.active_track.pk)
        self.assertEqual(track.pk, self.active_track.pk)
        self.assertEqual(
            [module.title for module in track.active_modules], ["Modulo activo"]
        )
        self.assertIn("revision", track.get_deferred_fields())
        self.assertIn("revision", track.active_modules[0].get_deferred_fields())

    def test_active_module_requires_active_matching_parent_in_one_query(self):
        with self.assertNumQueries(1):
            module = get_active_module(self.active_track.pk, self.active_module.pk)
        self.assertEqual(module.pk, self.active_module.pk)
        self.assertIsNone(get_active_module(self.first_track.pk, self.active_module.pk))
        self.assertIsNone(get_active_track(self.inactive_track.pk))
