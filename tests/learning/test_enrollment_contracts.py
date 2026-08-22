"""Contract tests for enrollment services."""

import inspect

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import Account
from catalog.models import Track
from learning.models import Enrollment
from learning.services.enrollment import enroll, get_enrollment, list_enrollments
from tests.factories.catalog import module_factory


class EnrollmentContractTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="enrollment@example.com",
            display_name="Enrollment Learner",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="Enrollment Track",
            description="Description",
            audience="Learners",
            position=1,
        )

    def test_public_signatures_are_stable(self):
        self.assertEqual(
            tuple(inspect.signature(enroll).parameters), ("account", "track")
        )
        self.assertEqual(
            tuple(inspect.signature(get_enrollment).parameters), ("account", "track")
        )
        self.assertEqual(
            tuple(inspect.signature(list_enrollments).parameters), ("account",)
        )

    def test_enroll_is_a_side_effect_free_stub(self):
        # After implementing enroll, it should create or return the unique Enrollment
        result = enroll(self.account, self.track)
        self.assertIsNotNone(result)
        self.assertTrue(
            Enrollment.objects.filter(account=self.account, track=self.track).exists()
        )

    def test_get_and_list_enrollments_are_deterministic_and_eager(self):
        other_track = Track.objects.create(
            title="Second Track",
            description="Description",
            audience="Learners",
            position=2,
        )
        first = Enrollment.objects.create(account=self.account, track=self.track)
        second = Enrollment.objects.create(account=self.account, track=other_track)

        self.assertEqual(get_enrollment(self.account, self.track), first)
        self.assertIsNone(
            get_enrollment(
                Account.objects.create_user(
                    email="other@example.com",
                    display_name="Other",
                    password="Strong-test-password-123",
                ),
                self.track,
            )
        )
        queryset = list_enrollments(self.account)
        self.assertEqual(list(queryset), [first, second])
        self.assertIn("track", queryset.query.select_related)

    def test_list_enrollments_publishes_module_count_with_bounded_queries(self):
        other_track = Track.objects.create(
            title="Track Without Modules",
            description="Description",
            audience="Learners",
            position=2,
        )
        module_factory(track=self.track, title="First Module", position=1)
        module_factory(track=self.track, title="Second Module", position=2)
        Enrollment.objects.create(account=self.account, track=self.track)
        Enrollment.objects.create(account=self.account, track=other_track)

        with self.assertNumQueries(2):
            enrollments = list(list_enrollments(self.account))

        self.assertEqual(
            [(item.track.title, item.module_count) for item in enrollments],
            [("Enrollment Track", 2), ("Track Without Modules", 0)],
        )

    def test_list_enrollments_revalidates_persisted_active_state(self):
        Account.objects.filter(pk=self.account.pk).update(is_active=False)

        with self.assertRaises(PermissionDenied):
            list_enrollments(self.account)
