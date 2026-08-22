"""Contract tests for daily-session service boundaries."""

import inspect

from django.test import SimpleTestCase

from learning.services.session import get_next_content_version, is_track_completed


class SessionContractTests(SimpleTestCase):
    def test_public_signatures_are_stable(self):
        self.assertEqual(
            tuple(inspect.signature(get_next_content_version).parameters),
            ("enrollment",),
        )
        self.assertEqual(
            tuple(inspect.signature(is_track_completed).parameters), ("enrollment",)
        )

    def test_session_operations_are_side_effect_free_stubs(self):
        enrollment = object()
        with self.assertRaises(NotImplementedError):
            get_next_content_version(enrollment)
        with self.assertRaises(NotImplementedError):
            is_track_completed(enrollment)
