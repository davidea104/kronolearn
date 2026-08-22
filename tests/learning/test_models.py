"""Persistence tests for learning domain contracts."""

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import Choice, ContentItem, ContentVersion, Module, Track
from learning.models import Attempt, Enrollment, Progress
from tests.factories.learning import (
    attempt_factory,
    enrollment_factory,
    progress_factory,
)


class LearningModelTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password="Strong-test-password-123",
        )
        self.track = Track.objects.create(
            title="Learning Track",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.module = Module.objects.create(
            track=self.track,
            title="Learning Module",
            objective="Objetivo",
            position=1,
        )
        self.item = ContentItem.objects.create(module=self.module, position=1)
        self.version = ContentVersion.objects.create(
            content_item=self.item,
            version_number=1,
            title="Version",
            learning_objective="Aprender",
            lesson_text="Leccion",
            case_prompt="Caso",
            source="Fuente",
            author=self.account,
            reviewed_on=timezone.localdate(),
        )
        self.choice = Choice.objects.create(
            content_version=self.version,
            text="Respuesta",
            position=1,
            rating=Choice.Rating.OPTIMAL,
            consequence="Consecuencia",
            explanation="Explicacion",
        )
        self.enrollment = Enrollment.objects.create(
            account=self.account,
            track=self.track,
        )

    def test_enrollment_is_unique_per_account_and_track(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(account=self.account, track=self.track)

    def test_attempt_digest_and_first_scoreable_are_unique(self):
        Attempt.objects.create(
            enrollment=self.enrollment,
            content_version=self.version,
            choice=self.choice,
            rating=self.choice.rating,
            is_first_scoreable=True,
            idempotency_digest="a" * 64,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Attempt.objects.create(
                enrollment=self.enrollment,
                content_version=self.version,
                choice=self.choice,
                rating=self.choice.rating,
                idempotency_digest="a" * 64,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Attempt.objects.create(
                enrollment=self.enrollment,
                content_version=self.version,
                choice=self.choice,
                rating=self.choice.rating,
                is_first_scoreable=True,
                idempotency_digest="b" * 64,
            )

    def test_progress_rejects_completed_above_total(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Progress.objects.create(
                enrollment=self.enrollment,
                module=self.module,
                completed_items=2,
                total_items=1,
            )

    def test_learning_factories_create_valid_defaults_and_accept_overrides(self):
        enrollment = enrollment_factory(status=Enrollment.Status.WITHDRAWN)
        attempt = attempt_factory(enrollment=enrollment, is_first_scoreable=True)
        progress = progress_factory(
            enrollment=enrollment, completed_items=1, total_items=2
        )

        self.assertEqual(enrollment.status, Enrollment.Status.WITHDRAWN)
        self.assertEqual(attempt.enrollment, enrollment)
        self.assertTrue(attempt.is_first_scoreable)
        self.assertEqual(progress.enrollment, enrollment)
        self.assertEqual(progress.completed_items, 1)
