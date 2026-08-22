"""Contract tests for enrollment services."""

import inspect

from django.test import TestCase

from accounts.models import Account
from catalog.models import Track
from learning.models import Enrollment
from learning.services.enrollment import enroll, get_enrollment, list_enrollments


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
