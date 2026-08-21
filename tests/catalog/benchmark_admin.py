"""Opt-in PostgreSQL benchmark for catalog administration SC-008."""

import json
import os
from statistics import quantiles
from time import perf_counter
from unittest import skipUnless

from django.contrib.auth.models import Group
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import CatalogState, Module, Track, canonicalize_title

RUN_BENCHMARK = os.environ.get("RUN_CATALOG_BENCHMARK") == "1"


@skipUnless(
    RUN_BENCHMARK and connection.vendor == "postgresql",
    "Set RUN_CATALOG_BENCHMARK=1 with PostgreSQL to run SC-008",
)
class CatalogAdminBenchmark(TransactionTestCase):
    """Measure 20 excluded warm-ups and 200 balanced administrative requests."""

    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.actor = Account.objects.create_user(
            email="benchmark@example.com",
            display_name="Benchmark Admin",
            password="Benchmark-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        cls.actor.groups.add(content_group)
        tracks = [
            Track(
                title=f"Benchmark track {index}",
                title_key=canonicalize_title(f"Benchmark track {index}"),
                description="Benchmark description",
                audience="Benchmark audience",
                position=index,
            )
            for index in range(1, 101)
        ]
        Track.objects.bulk_create(tracks)
        persisted_tracks = list(Track.objects.order_by("position"))
        modules = []
        for track in persisted_tracks:
            modules.extend(
                Module(
                    track=track,
                    title=f"Benchmark module {index}",
                    title_key=canonicalize_title(f"Benchmark module {index}"),
                    objective="Benchmark objective",
                    position=index,
                    status=Module.Status.ACTIVE,
                    published_version=1,
                )
                for index in range(1, 51)
            )
        Module.objects.bulk_create(modules)
        cls.tracks = persisted_tracks

    def setUp(self):
        self.client.force_login(self.actor)
        self.sequence = 0

    def _create(self):
        self.sequence += 1
        return self.client.post(
            reverse("catalog:manage-track-create"),
            {
                "title": f"Created benchmark track {self.sequence}",
                "description": "Benchmark description",
                "audience": "Benchmark audience",
            },
        )

    def _edit(self):
        track = self.tracks[self.sequence % 50]
        track.refresh_from_db()
        self.sequence += 1
        return self.client.post(
            reverse("catalog:manage-track-edit", kwargs={"track_ref": track.pk}),
            {
                "title": f"Edited benchmark track {track.position}-{self.sequence}",
                "description": "Benchmark description",
                "audience": "Benchmark audience",
                "expected_revision": track.revision,
            },
        )

    def _reorder(self):
        track = self.tracks[50 + (self.sequence % 25)]
        order_revision = CatalogState.objects.get(pk=1).track_order_revision
        self.sequence += 1
        return self.client.post(
            reverse("catalog:manage-track-reorder", kwargs={"track_ref": track.pk}),
            {"position": 1, "expected_order_revision": order_revision},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="track-rows",
        )

    def _state(self):
        track = self.tracks[75 + (self.sequence % 25)]
        track.refresh_from_db()
        self.sequence += 1
        return self.client.post(
            reverse("catalog:manage-track-activate", kwargs={"track_ref": track.pk}),
            {
                "expected_revision": track.revision,
                "source": "BENCHMARK-DOC",
                "reviewed_on": timezone.localdate().isoformat(),
                "editorial_status": "APPROVED",
            },
        )

    def _run_request(self, operation):
        started = perf_counter()
        response = operation()
        elapsed = perf_counter() - started
        self.assertIn(response.status_code, (200, 303))
        return elapsed

    def test_sc008_admin_request_p95(self):
        operations = (self._create, self._edit, self._reorder, self._state)
        for index in range(20):
            self._run_request(operations[index % 4])

        observations = {
            operation.__name__.removeprefix("_"): [] for operation in operations
        }
        measured = []
        for operation in operations:
            for _ in range(50):
                elapsed = self._run_request(operation)
                observations[operation.__name__.removeprefix("_")].append(elapsed)
                measured.append(elapsed)

        report = {
            "database": connection.vendor,
            "warmups_excluded": 20,
            "measured_requests": len(measured),
            "p95_seconds": quantiles(measured, n=100, method="inclusive")[94],
            "family_p95_seconds": {
                name: quantiles(values, n=100, method="inclusive")[94]
                for name, values in observations.items()
            },
            "observations_seconds": observations,
        }
        print(json.dumps(report, sort_keys=True))
        self.assertLess(report["p95_seconds"], 2.0, json.dumps(report, sort_keys=True))
