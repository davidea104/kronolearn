"""Tests for the health-check contract."""

from unittest.mock import patch

from django.db.utils import DatabaseError
from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    """Verify the public health-check response contract."""

    def test_returns_ok_when_postgresql_is_available(self):
        with patch("kronolearn.health.connection") as mock_connection:
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Content-Type"], "application/json")
        mock_connection.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            "SELECT 1"
        )

    def test_returns_degraded_when_postgresql_is_unavailable(self):
        with patch("kronolearn.health.connection") as mock_connection:
            mock_connection.cursor.side_effect = DatabaseError
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "degraded"})
        self.assertEqual(response["Content-Type"], "application/json")
        mock_connection.cursor.assert_called_once_with()
