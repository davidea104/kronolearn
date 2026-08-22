"""Contract tests for progress projections."""

import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal

from django.test import SimpleTestCase

from learning.services.progress import (
    TrackProgress,
    get_track_progress,
    recompute_progress,
)


class ProgressContractTests(SimpleTestCase):
    def test_track_progress_is_frozen_and_validates_percentage(self):
        projection = TrackProgress(percentage=Decimal(0), modules=(), accuracy=None)
        self.assertIsNone(projection.accuracy)
        with self.assertRaises(FrozenInstanceError):
            projection.percentage = Decimal(50)
        for value in (Decimal("-0.01"), Decimal("100.01")):
            with self.assertRaises(ValueError):
                TrackProgress(percentage=value, modules=(), accuracy=None)

    def test_public_signatures_and_stubs(self):
        self.assertEqual(
            tuple(inspect.signature(recompute_progress).parameters), ("enrollment",)
        )
        self.assertEqual(
            tuple(inspect.signature(get_track_progress).parameters), ("enrollment",)
        )
        with self.assertRaises(NotImplementedError):
            recompute_progress(object())
        with self.assertRaises(NotImplementedError):
            get_track_progress(object())
