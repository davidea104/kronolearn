"""Progressive dual-scope login throttling contracts."""

import importlib
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

from django.db import connection, connections
from django.test import RequestFactory, TransactionTestCase, skipUnlessDBFeature
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from accounts.forms import ThrottledAuthenticationForm
from accounts.models import LoginThrottleBucket
from accounts.security import security_digest


class LoginThrottleTests(TransactionTestCase):
    reset_sequences = True

    def service(self):
        try:
            return importlib.import_module("accounts.services.throttling")
        except ModuleNotFoundError as exc:
            self.fail(f"Throttle service is missing: {exc.name}")

    def test_failures_progress_from_one_second_to_sixty_second_cap(self):
        service = self.service()
        now = timezone.now()
        delays = []

        for attempt in range(1, 8):
            delays.append(
                service.record_login_failure(
                    "learner@example.com",
                    "127.0.0.1",
                    now=now + timedelta(seconds=attempt * 61),
                )
            )

        self.assertEqual(delays, [1, 2, 4, 8, 16, 32, 60])
        self.assertEqual(LoginThrottleBucket.objects.count(), 2)

    def test_effective_delay_uses_both_account_and_origin_scopes(self):
        service = self.service()
        now = timezone.now()
        service.record_login_failure("learner@example.com", "127.0.0.1", now=now)

        self.assertEqual(
            service.evaluate_login_throttle(
                "learner@example.com",
                "127.0.0.1",
                now=now,
            ),
            1,
        )
        self.assertEqual(
            set(LoginThrottleBucket.objects.values_list("scope", flat=True)),
            {"ACCOUNT", "ORIGIN"},
        )

    def test_evaluation_filters_both_exact_digests_in_sql(self):
        service = self.service()
        email = "learner@example.com"
        origin = "127.0.0.1"
        account_digest = security_digest(email, purpose="login-account")
        origin_digest = security_digest(origin, purpose="login-origin")

        with CaptureQueriesContext(connection) as queries:
            service.evaluate_login_throttle(email, origin)

        select_queries = [
            query["sql"]
            for query in queries.captured_queries
            if "SELECT" in query["sql"].upper()
            and "accounts_loginthrottlebucket" in query["sql"]
        ]
        self.assertTrue(select_queries)
        self.assertIn(account_digest, select_queries[-1])
        self.assertIn(origin_digest, select_queries[-1])

    def test_evaluation_prunes_expired_buckets(self):
        service = self.service()
        now = timezone.now()
        LoginThrottleBucket.objects.create(
            scope=LoginThrottleBucket.Scope.ACCOUNT,
            key_digest=uuid.uuid4().hex * 2,
            failure_count=3,
            last_failed_at=now - timedelta(minutes=16),
            blocked_until=now - timedelta(minutes=15),
        )

        service.evaluate_login_throttle("learner@example.com", "127.0.0.1", now=now)

        self.assertEqual(LoginThrottleBucket.objects.count(), 0)

    def test_inactivity_resets_failure_count(self):
        service = self.service()
        now = timezone.now()
        service.record_login_failure("learner@example.com", "127.0.0.1", now=now)

        delay = service.record_login_failure(
            "learner@example.com",
            "127.0.0.1",
            now=now + timedelta(minutes=16),
        )

        self.assertEqual(delay, 1)
        self.assertTrue(
            all(
                count == 1
                for count in LoginThrottleBucket.objects.values_list(
                    "failure_count", flat=True
                )
            )
        )

    def test_success_clears_only_account_bucket(self):
        service = self.service()
        now = timezone.now()
        service.record_login_failure("learner@example.com", "127.0.0.1", now=now)

        service.record_login_success("learner@example.com")

        self.assertFalse(LoginThrottleBucket.objects.filter(scope="ACCOUNT").exists())
        self.assertTrue(LoginThrottleBucket.objects.filter(scope="ORIGIN").exists())

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_first_failures_share_one_bucket_per_scope(self):
        service = self.service()
        barrier = threading.Barrier(2)
        now = timezone.now()

        def fail_login():
            connections.close_all()
            try:
                barrier.wait()
                return service.record_login_failure(
                    "learner@example.com", "127.0.0.1", now=now
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            delays = [
                future.result()
                for future in [executor.submit(fail_login) for _ in range(2)]
            ]

        self.assertEqual(sorted(delays), [1, 2])
        self.assertEqual(LoginThrottleBucket.objects.count(), 2)
        self.assertEqual(
            set(
                LoginThrottleBucket.objects.values_list(
                    "failure_count",
                    flat=True,
                )
            ),
            {2},
        )
        self.assertEqual(connection.vendor, "postgresql")

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_forms_allow_only_one_credential_evaluation(self):
        first_entered = threading.Event()
        release_first = threading.Event()
        second_entered = threading.Event()
        call_count = 0
        count_lock = threading.Lock()

        def fake_authenticate(request, username, password):
            nonlocal call_count
            with count_lock:
                call_count += 1
                current_call = call_count
            if current_call == 1:
                first_entered.set()
                release_first.wait(timeout=2)
            else:
                second_entered.set()

        def submit_form():
            connections.close_all()
            request = RequestFactory().post(
                "/accounts/login/",
                REMOTE_ADDR="127.0.0.1",
            )
            try:
                with patch("accounts.forms.authenticate", fake_authenticate):
                    form = ThrottledAuthenticationForm(
                        request,
                        data={
                            "username": "learner@example.com",
                            "password": "wrong-password-value",
                        },
                    )
                    return form.is_valid()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(submit_form)
            self.assertTrue(first_entered.wait(timeout=2))
            second = executor.submit(submit_form)
            bypassed_serialization = second_entered.wait(timeout=0.25)
            release_first.set()
            self.assertFalse(first.result())
            self.assertFalse(second.result())

        self.assertFalse(bypassed_serialization)
        self.assertEqual(call_count, 1)
        self.assertEqual(
            LoginThrottleBucket.objects.get(
                scope=LoginThrottleBucket.Scope.ACCOUNT
            ).failure_count,
            1,
        )
