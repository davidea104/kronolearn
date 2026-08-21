"""Registration behavior and concurrency contracts."""

import threading

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import NoReverseMatch, reverse

VALID_PASSWORD = "correct-horse-battery-staple"


def registration_url(test_case):
    try:
        return reverse("accounts:register")
    except NoReverseMatch:
        test_case.fail("accounts:register route must exist")


class RegistrationViewTests(TestCase):
    def test_valid_registration_creates_canonical_learner_and_redirects(self):
        response = self.client.post(
            registration_url(self),
            {
                "email": "  Learner@Example.COM ",
                "display_name": " Learner One ",
                "password1": VALID_PASSWORD,
                "password2": VALID_PASSWORD,
            },
        )

        account = get_user_model().objects.get()
        self.assertEqual(response.status_code, 303)
        self.assertEqual(account.email, "learner@example.com")
        self.assertEqual(account.display_name, "Learner One")
        self.assertEqual(
            set(account.groups.values_list("name", flat=True)),
            {"learner"},
        )
        self.assertFalse(account.is_superuser)

    def test_invalid_registration_creates_no_partial_account(self):
        response = self.client.post(
            registration_url(self),
            {
                "email": "not-an-email",
                "display_name": "",
                "password1": "short",
                "password2": "different",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertContains(response, "error-summary")

    def test_duplicate_canonical_email_gets_generic_rejection(self):
        get_user_model().objects.create_user(
            email="learner@example.com",
            display_name="Existing",
            password=VALID_PASSWORD,
        )

        response = self.client.post(
            registration_url(self),
            {
                "email": " LEARNER@EXAMPLE.COM ",
                "display_name": "Duplicate",
                "password1": VALID_PASSWORD,
                "password2": VALID_PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No fue posible crear la cuenta")
        self.assertEqual(get_user_model().objects.count(), 1)


class ConcurrentRegistrationTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_simultaneous_equivalent_emails_create_at_most_one_account(self):
        from accounts.services.registration import register_account

        barrier = threading.Barrier(2)
        outcomes = []

        def register(email):
            connections.close_all()
            barrier.wait()
            try:
                register_account(
                    email=email,
                    display_name="Concurrent",
                    password=VALID_PASSWORD,
                )
                outcomes.append("created")
            except IntegrityError:
                outcomes.append("duplicate")
            finally:
                connections.close_all()

        threads = [
            threading.Thread(target=register, args=("learner@example.com",)),
            threading.Thread(target=register, args=(" LEARNER@EXAMPLE.COM ",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertCountEqual(outcomes, ["created", "duplicate"])
        self.assertEqual(connection.vendor, "postgresql")
