"""Command-boundary tests for deployment learning-content loading."""

from contextlib import redirect_stderr
from importlib import import_module
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import SimpleTestCase, override_settings
from django.test.utils import CaptureQueriesContext

from catalog.content_data import load_definitions
from catalog.services.content import ContentLoadConflict


class LoadLearningContentCommandTests(SimpleTestCase):
    databases = frozenset({"default"})

    @staticmethod
    def command_module():
        return import_module("catalog.management.commands.load_learning_content")

    def test_parser_rejects_actor_identity_argument(self):
        parser = (
            self.command_module()
            .Command()
            .create_parser("manage.py", "load_learning_content")
        )

        with redirect_stderr(StringIO()), self.assertRaises(CommandError):
            parser.parse_args(["--actor-id", "private-account-reference"])

    @override_settings(CONTENT_AUTHOR_ACCOUNT_ID="private-account-reference")
    def test_command_uses_setting_reports_counts_and_does_not_query_models(self):
        module = self.command_module()
        definitions = load_definitions()
        outcomes = iter(
            (
                SimpleNamespace(
                    changed=True,
                    track_count=2,
                    module_count=2,
                    content_item_count=10,
                    items_created=10,
                    versions_created=10,
                ),
                SimpleNamespace(
                    changed=False,
                    track_count=2,
                    module_count=2,
                    content_item_count=10,
                    items_created=0,
                    versions_created=0,
                ),
            )
        )
        received = []

        def fake_load(actor_ref, loaded_definitions):
            received.append((actor_ref, loaded_definitions))
            return next(outcomes)

        first_output = StringIO()
        second_output = StringIO()
        with (
            CaptureQueriesContext(connection) as queries,
            self.settings(CONTENT_AUTHOR_ACCOUNT_ID="private-account-reference"),
            patch.object(module, "load_definitions", return_value=definitions),
            patch.object(module, "load_learning_content", side_effect=fake_load),
        ):
            call_command("load_learning_content", stdout=first_output)
            call_command("load_learning_content", stdout=second_output)

        self.assertEqual(len(queries), 0)
        self.assertEqual(
            received,
            [
                ("private-account-reference", definitions),
                ("private-account-reference", definitions),
            ],
        )
        self.assertIn("2 tracks", first_output.getvalue())
        self.assertIn("2 módulos", first_output.getvalue())
        self.assertIn("10 unidades", first_output.getvalue())
        self.assertIn("10 unidades creadas", first_output.getvalue())
        self.assertIn("10 versiones creadas", first_output.getvalue())
        self.assertIn("0 unidades creadas", second_output.getvalue())
        self.assertIn("0 versiones creadas", second_output.getvalue())
        self.assertNotIn("private-account-reference", first_output.getvalue())
        self.assertNotIn("private-account-reference", second_output.getvalue())

    @override_settings(CONTENT_AUTHOR_ACCOUNT_ID=None)
    def test_missing_configuration_fails_before_loading(self):
        module = self.command_module()
        with (
            patch.object(module, "load_definitions") as parser,
            self.assertRaises(CommandError) as raised,
        ):
            call_command("load_learning_content")

        parser.assert_not_called()
        self.assertNotIn("CONTENT_AUTHOR_ACCOUNT_ID", str(raised.exception))

    @override_settings(CONTENT_AUTHOR_ACCOUNT_ID="private-account-reference")
    def test_expected_failures_are_sanitized(self):
        module = self.command_module()
        private_values = (
            "private-account-reference",
            "author@example.invalid",
            "postgresql://secret@localhost/database",
        )
        for error in (
            PermissionDenied("author@example.invalid"),
            ValidationError("private-account-reference"),
            ContentLoadConflict("postgresql://secret@localhost/database"),
        ):
            with self.subTest(error=type(error).__name__):
                with (
                    patch.object(module, "load_definitions", return_value=()),
                    patch.object(module, "load_learning_content", side_effect=error),
                    self.assertRaises(CommandError) as raised,
                ):
                    call_command("load_learning_content")

                message = str(raised.exception)
                self.assertTrue(message)
                self.assertTrue(raised.exception.__suppress_context__)
                self.assertIsNone(raised.exception.__cause__)
                for private_value in private_values:
                    self.assertNotIn(private_value, message)
