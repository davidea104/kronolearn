"""Privacy and digest contract evidence for shared domain boundaries."""

import inspect
from dataclasses import fields
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.db import models
from django.test import SimpleTestCase, TestCase, override_settings

from accounts.models import Account
from accounts.security import security_digest
from analytics.services.metrics import ContentMetrics, EngagementMetrics
from gamification.models import ScoreEvent
from gamification.services.scoring import award_for_attempt
from learning.models import Attempt
from learning.services.attempts import register_attempt
from learning.signals import session_completed


class DomainPrivacyContractTests(SimpleTestCase):
    @override_settings(SECRET_KEY="privacy-test-secret")
    def test_security_digest_is_deterministic_and_purpose_separated(self):
        value = "opaque-caller-key"
        first = security_digest(value, purpose="learning.attempt.idempotency")
        second = security_digest(value, purpose="learning.attempt.idempotency")
        other = security_digest(value, purpose="gamification.score-event.idempotency")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(len(first), 64)
        self.assertNotIn(value, first)

    def test_stub_docs_name_exact_digest_inputs_and_purposes(self):
        attempt_doc = inspect.getdoc(register_attempt) or ""
        score_doc = inspect.getdoc(award_for_attempt) or ""
        self.assertIn(
            'security_digest(idempotency_key, purpose="learning.attempt.idempotency")',
            attempt_doc,
        )
        self.assertIn("security_digest(str(attempt.id)", score_doc)
        self.assertIn('purpose="gamification.score-event.idempotency")', score_doc)

    def test_raw_idempotency_inputs_have_no_persistence_field(self):
        for model in (Attempt, ScoreEvent):
            field_names = {field.name for field in model._meta.get_fields()}
            self.assertIn("idempotency_digest", field_names)
            self.assertNotIn("idempotency_key", field_names)

    def test_public_projections_contain_no_account_identifiers(self):
        for projection in (ContentMetrics, EngagementMetrics):
            names = {field.name for field in fields(projection)}
            self.assertFalse(names & {"email", "account", "account_id", "user_id"})

    def test_session_event_transports_only_the_predigested_value(self):
        captured = []

        def capture(sender, enrollment, completed_at, idempotency_key, **kwargs):
            captured.append(idempotency_key)

        digest = "f" * 64
        session_completed.connect(
            capture, weak=False, dispatch_uid="tests.privacy.capture"
        )
        try:
            session_completed.send(
                sender=self,
                enrollment=object(),
                completed_at=object(),
                idempotency_key=digest,
            )
        finally:
            session_completed.disconnect(dispatch_uid="tests.privacy.capture")
        self.assertEqual(captured, [digest])


@override_settings(DEBUG=True)
class DemoPrivacyContractTests(TestCase):
    def test_demo_emails_exist_only_in_authoritative_account_fields(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertNotIn(".invalid", output.getvalue().casefold())

        demo_emails = tuple(
            Account.objects.filter(email__endswith=".invalid").values_list(
                "email", flat=True
            )
        )
        self.assertEqual(len(demo_emails), 2)
        for model in apps.get_models():
            for field in model._meta.concrete_fields:
                if not isinstance(field, (models.CharField, models.TextField)):
                    continue
                if model is Account and field.name == "email":
                    continue
                values = model.objects.values_list(field.name, flat=True)
                for value in values:
                    self.assertNotIn(".invalid", str(value).casefold())
