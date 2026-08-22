"""Contract tests for synchronous domain-event envelopes and subscriptions."""

from unittest.mock import patch

from django.db import transaction
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Account
from catalog.models import Track
from gamification.apps import GamificationConfig
from gamification.models import ScoreEvent, Streak
from learning.apps import LearningConfig
from learning.models import Enrollment
from learning.signals import attempt_registered, session_completed


def _sync_receivers(signal):
    return signal._live_receivers(sender=None)[0]


class DomainSignalContractTests(SimpleTestCase):
    def tearDown(self):
        attempt_registered.disconnect(dispatch_uid="tests.first")
        attempt_registered.disconnect(dispatch_uid="tests.second")
        session_completed.disconnect(dispatch_uid="tests.capture")

    def test_attempt_envelope_is_named_ordered_and_propagates_errors(self):
        calls = []

        def first(sender, attempt, result, **kwargs):
            calls.append(("first", sender, attempt, result))

        def second(sender, attempt, result, **kwargs):
            calls.append(("second", sender, attempt, result))
            raise RuntimeError("receiver failure")

        attempt_registered.connect(first, weak=False, dispatch_uid="tests.first")
        attempt_registered.connect(second, weak=False, dispatch_uid="tests.second")

        with self.assertRaisesMessage(RuntimeError, "receiver failure"):
            attempt_registered.send(sender=self, attempt="attempt", result="result")
        self.assertEqual(
            [call[0] for call in calls if call[0] in {"first", "second"}],
            ["first", "second"],
        )
        self.assertEqual(calls[-1][2:], ("attempt", "result"))

    def test_session_envelope_delivers_prederived_digest_unchanged(self):
        captured = []

        def capture(sender, enrollment, completed_at, idempotency_key, **kwargs):
            captured.append((enrollment, completed_at, idempotency_key))

        session_completed.connect(capture, weak=False, dispatch_uid="tests.capture")
        digest = "d" * 64
        session_completed.send(
            sender=self,
            enrollment="enrollment",
            completed_at="completed-at",
            idempotency_key=digest,
        )
        self.assertEqual(captured, [("enrollment", "completed-at", digest)])

    def test_ready_is_idempotent_and_subscription_matrix_is_exact(self):
        learning_config = LearningConfig("learning", __import__("learning"))
        gamification_config = GamificationConfig(
            "gamification", __import__("gamification")
        )
        learning_config.ready()
        gamification_config.ready()
        before = (
            tuple(_sync_receivers(attempt_registered)),
            tuple(_sync_receivers(session_completed)),
        )
        learning_config.ready()
        gamification_config.ready()
        after = (
            tuple(_sync_receivers(attempt_registered)),
            tuple(_sync_receivers(session_completed)),
        )
        self.assertEqual(after, before)

        attempt_modules = [receiver.__module__ for receiver in before[0]]
        session_modules = [receiver.__module__ for receiver in before[1]]
        self.assertEqual(attempt_modules.count("learning.receivers"), 1)
        self.assertEqual(attempt_modules.count("gamification.receivers"), 3)
        self.assertNotIn("learning.receivers", session_modules)
        self.assertEqual(session_modules.count("gamification.receivers"), 1)

    def test_signal_delivery_is_synchronous(self):
        calls = []

        def capture(sender, attempt, result, **kwargs):
            calls.append("called")

        with patch.object(attempt_registered, "send", wraps=attempt_registered.send):
            attempt_registered.connect(capture, weak=False, dispatch_uid="tests.first")
            attempt_registered.send(sender=self, attempt=object(), result=object())
        self.assertIn("called", calls)


class TransactionalSignalContractTests(TransactionTestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="signal@example.com",
            display_name="Signal Learner",
            password="Strong-test-password-123",
        )
        track = Track.objects.create(
            title="Signal Track",
            description="Description",
            audience="Learners",
            position=1,
        )
        self.enrollment = Enrollment.objects.create(account=self.account, track=track)

    def tearDown(self):
        for signal in (attempt_registered, session_completed):
            signal.disconnect(dispatch_uid="tests.transaction.writer")
            signal.disconnect(dispatch_uid="tests.transaction.failure")

    def test_attempt_receiver_failure_rolls_back_prior_receiver_write(self):
        def writer(sender, attempt, result, **kwargs):
            Streak.objects.create(account=self.account)

        def failure(sender, attempt, result, **kwargs):
            raise RuntimeError("rollback attempt event")

        attempt_registered.connect(
            writer, weak=False, dispatch_uid="tests.transaction.writer"
        )
        attempt_registered.connect(
            failure, weak=False, dispatch_uid="tests.transaction.failure"
        )
        with (
            self.assertRaisesMessage(RuntimeError, "rollback attempt event"),
            transaction.atomic(),
        ):
            attempt_registered.send(sender=self, attempt=object(), result=object())
        self.assertFalse(Streak.objects.exists())

    def test_session_receiver_failure_rolls_back_prior_receiver_write(self):
        digest = "e" * 64

        def writer(sender, enrollment, completed_at, idempotency_key, **kwargs):
            ScoreEvent.objects.create(
                cause=ScoreEvent.Cause.SESSION_COMPLETED,
                amount=0,
                idempotency_digest=idempotency_key,
            )

        def failure(sender, enrollment, completed_at, idempotency_key, **kwargs):
            raise RuntimeError("rollback session event")

        session_completed.connect(
            writer, weak=False, dispatch_uid="tests.transaction.writer"
        )
        session_completed.connect(
            failure, weak=False, dispatch_uid="tests.transaction.failure"
        )
        with (
            self.assertRaisesMessage(RuntimeError, "rollback session event"),
            transaction.atomic(),
        ):
            session_completed.send(
                sender=self,
                enrollment=self.enrollment,
                completed_at=timezone.now(),
                idempotency_key=digest,
            )
        self.assertFalse(ScoreEvent.objects.filter(idempotency_digest=digest).exists())
