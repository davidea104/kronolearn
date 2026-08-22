"""Contract tests for immutable attempt projections and queries."""

import inspect
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from threading import Barrier
from unittest import skipUnless

from django.db import IntegrityError, close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import Choice, ContentItem, ContentVersion, Module, Track
from learning.models import Attempt, Enrollment
from learning.services.attempts import AttemptResult, list_attempts, register_attempt


class AttemptContractTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="attempt@example.com",
            display_name="Attempt Learner",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="Attempt Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        module = Module.objects.create(
            track=self.track, title="Module", objective="Objective", position=1
        )
        item = ContentItem.objects.create(module=module, position=1)
        self.version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Version",
            learning_objective="Learn",
            lesson_text="Lesson",
            case_prompt="Case",
            source="Source",
            author=self.account,
            reviewed_on=timezone.localdate(),
        )
        self.choice = Choice.objects.create(
            content_version=self.version,
            text="Choice",
            position=1,
            rating=Choice.Rating.OPTIMAL,
            consequence="Consequence",
            explanation="Explanation",
        )
        self.enrollment = Enrollment.objects.create(
            account=self.account, track=self.track
        )

    def test_attempt_result_is_frozen(self):
        attempt = Attempt(
            enrollment=self.enrollment,
            content_version=self.version,
            choice=self.choice,
            rating=self.choice.rating,
            idempotency_digest="a" * 64,
        )
        result = AttemptResult(
            attempt=attempt,
            rating=self.choice.rating,
            is_scoreable=True,
            consequence=self.choice.consequence,
            explanation=self.choice.explanation,
            source=self.version.source,
        )
        with self.assertRaises(FrozenInstanceError):
            result.rating = Choice.Rating.INCORRECT

    def test_public_signatures_and_side_effect_free_stub(self):
        self.assertEqual(
            tuple(inspect.signature(register_attempt).parameters),
            ("enrollment", "content_version", "choice", "idempotency_key"),
        )
        self.assertEqual(
            tuple(inspect.signature(list_attempts).parameters), ("enrollment",)
        )
        with self.assertRaises(NotImplementedError):
            register_attempt(self.enrollment, self.version, self.choice, "opaque")
        self.assertFalse(Attempt.objects.exists())

    def test_list_attempts_is_ordered_and_eager(self):
        first = Attempt.objects.create(
            enrollment=self.enrollment,
            content_version=self.version,
            choice=self.choice,
            rating=self.choice.rating,
            idempotency_digest="a" * 64,
        )
        second = Attempt.objects.create(
            enrollment=self.enrollment,
            content_version=self.version,
            choice=self.choice,
            rating=self.choice.rating,
            idempotency_digest="b" * 64,
        )
        queryset = list_attempts(self.enrollment)
        self.assertEqual(list(queryset), [first, second])
        self.assertIn("content_version", queryset.query.select_related)
        self.assertIn("choice", queryset.query.select_related)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL concurrency evidence")
class PostgreSQLAttemptConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="attempt-race@example.com",
            display_name="Attempt Race",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="Attempt Race Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        module = Module.objects.create(
            track=self.track, title="Module", objective="Objective", position=1
        )
        item = ContentItem.objects.create(module=module, position=1)
        self.version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Version",
            learning_objective="Learn",
            lesson_text="Lesson",
            case_prompt="Case",
            source="Source",
            author=self.account,
            reviewed_on=timezone.localdate(),
        )
        self.choice = Choice.objects.create(
            content_version=self.version,
            text="Choice",
            position=1,
            rating=Choice.Rating.OPTIMAL,
            consequence="Consequence",
            explanation="Explanation",
        )
        self.enrollment = Enrollment.objects.create(
            account=self.account, track=self.track
        )

    def _race(self, create):
        barrier = Barrier(2)

        def worker():
            close_old_connections()
            barrier.wait()
            try:
                create()
                return "created"
            except IntegrityError:
                return "integrity"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return sorted(executor.map(lambda _: worker(), range(2)))

    def test_concurrent_enrollment_uniqueness(self):
        self.enrollment.delete()
        result = self._race(
            lambda: Enrollment.objects.create(
                account_id=self.account.pk, track_id=self.track.pk
            )
        )
        self.assertEqual(result, ["created", "integrity"])

    def test_concurrent_attempt_digest_uniqueness(self):
        result = self._race(
            lambda: Attempt.objects.create(
                enrollment_id=self.enrollment.pk,
                content_version_id=self.version.pk,
                choice_id=self.choice.pk,
                rating=self.choice.rating,
                idempotency_digest="d" * 64,
            )
        )
        self.assertEqual(result, ["created", "integrity"])

    def test_concurrent_first_scoreable_uniqueness(self):
        result = self._race(
            lambda: Attempt.objects.create(
                enrollment_id=self.enrollment.pk,
                content_version_id=self.version.pk,
                choice_id=self.choice.pk,
                rating=self.choice.rating,
                is_first_scoreable=True,
                idempotency_digest=__import__("uuid").uuid4().hex * 2,
            )
        )
        self.assertEqual(result, ["created", "integrity"])
