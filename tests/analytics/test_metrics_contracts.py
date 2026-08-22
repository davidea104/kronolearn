"""Contract tests for privacy-preserving metric projections."""

import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal

from django.test import SimpleTestCase

from analytics.services.metrics import (
    ContentMetrics,
    EngagementMetrics,
    content_metrics,
    engagement_metrics,
)


class MetricsContractTests(SimpleTestCase):
    def test_metric_projections_copy_values_into_immutable_mappings(self):
        values = {"completion_rate": Decimal("42.5")}
        projection = ContentMetrics(
            context="track", person_count=10, is_suppressed=False, values=values
        )
        values["completion_rate"] = Decimal(0)
        self.assertEqual(projection.values["completion_rate"], Decimal("42.5"))
        with self.assertRaises(TypeError):
            projection.values["completion_rate"] = Decimal(10)
        with self.assertRaises(FrozenInstanceError):
            projection.person_count = 11

    def test_suppressed_projection_has_no_values(self):
        projection = EngagementMetrics(
            context="30-days",
            person_count=2,
            is_suppressed=True,
            values={"active_people": 2},
        )
        self.assertEqual(dict(projection.values), {})

    def test_public_signatures_and_stubs(self):
        self.assertEqual(
            tuple(inspect.signature(content_metrics).parameters), ("track",)
        )
        self.assertIsNone(
            inspect.signature(content_metrics).parameters["track"].default
        )
        self.assertEqual(
            tuple(inspect.signature(engagement_metrics).parameters), ("window_days",)
        )
        with self.assertRaises(NotImplementedError):
            content_metrics()
        with self.assertRaises(NotImplementedError):
            engagement_metrics(30)
