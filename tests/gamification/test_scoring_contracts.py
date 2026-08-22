"""Contract tests for score-event services."""

import inspect
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.db import IntegrityError, close_old_connections, connection
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import Choice, ContentItem, ContentVersion, Module, Track
from gamification.models import ScoreEvent
from gamification.services.scoring import RATING_POINTS, award_for_attempt
from learning.models import Attempt, Enrollment


class ScoringContractTests(SimpleTestCase):
    def test_rating_points_are_complete_and_immutable(self):
        self.assertEqual(
            dict(RATING_POINTS),
            {
                Choice.Rating.OPTIMAL: 100,
                Choice.Rating.PARTIAL: 50,
                Choice.Rating.INCORRECT: 0,
            },
        )
        with self.assertRaises(TypeError):
            RATING_POINTS[Choice.Rating.OPTIMAL] = 0

    def test_public_signature_and_stub(self):
        self.assertEqual(
            tuple(inspect.signature(award_for_attempt).parameters), ("attempt",)
        )
        with self.assertRaises(NotImplementedError):
            award_for_attempt(object())


@skipUnless(connection.vendor == "postgresql", "PostgreSQL concurrency evidence")
class PostgreSQLScoringConcurrencyTests(TransactionTestCase):
    def setUp(self):
        account = Account.objects.create_user(
            email="score-race@example.com",
            display_name="Score Race",
            password="Strong-test-password-123",
        )
        track = Track.objects.create(
            title="Score Race Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        module = Module.objects.create(
            track=track, title="Module", objective="Objective", position=1
        )
        item = ContentItem.objects.create(module=module, position=1)
        version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            title="Version",
            learning_objective="Learn",
            lesson_text="Lesson",
            case_prompt="Case",
            source="Source",
            author=account,
            reviewed_on=timezone.localdate(),
        )
        choice = Choice.objects.create(
            content_version=version,
            text="Choice",
            position=1,
            rating=Choice.Rating.OPTIMAL,
            consequence="Consequence",
            explanation="Explanation",
        )
        enrollment = Enrollment.objects.create(account=account, track=track)
        self.attempts = tuple(
            Attempt.objects.create(
                enrollment=enrollment,
                content_version=version,
                choice=choice,
                rating=choice.rating,
                idempotency_digest=uuid4().hex * 2,
            )
            for _ in range(2)
        )

    def _race(self, create):
        barrier = Barrier(2)

        def worker(index):
            close_old_connections()
            barrier.wait()
            try:
                create(index)
                return "created"
            except IntegrityError:
                return "integrity"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return sorted(executor.map(worker, range(2)))

    def test_concurrent_score_digest_uniqueness(self):
        result = self._race(
            lambda index: ScoreEvent.objects.create(
                cause=ScoreEvent.Cause.ATTEMPT,
                amount=100,
                attempt_id=self.attempts[index].pk,
                idempotency_digest="s" * 64,
            )
        )
        self.assertEqual(result, ["created", "integrity"])

    def test_concurrent_one_event_per_attempt(self):
        result = self._race(
            lambda index: ScoreEvent.objects.create(
                cause=ScoreEvent.Cause.ATTEMPT,
                amount=100,
                attempt_id=self.attempts[0].pk,
                idempotency_digest=("a" if index == 0 else "b") * 64,
            )
        )
        self.assertEqual(result, ["created", "integrity"])
