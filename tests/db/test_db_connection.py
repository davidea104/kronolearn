"""Validación de DATABASE_URL y conectividad básica con PostgreSQL."""

import os
import unittest
from urllib.parse import urlparse

import psycopg


class DatabaseURLConnectionTests(unittest.TestCase):
    """Comprueba la configuración requerida para conectar a PostgreSQL."""

    def test_database_url_connects_and_executes_select_one(self) -> None:
        database_url = os.environ.get("DATABASE_URL")
        self.assertTrue(
            database_url, "DATABASE_URL debe estar definida para esta prueba."
        )

        parsed_url = urlparse(database_url)
        self.assertIn(
            parsed_url.scheme,
            {"postgresql", "postgres"},
            "DATABASE_URL debe usar el esquema postgresql:// o postgres://.",
        )
        self.assertTrue(
            parsed_url.hostname,
            "DATABASE_URL debe incluir un host de PostgreSQL.",
        )
        self.assertTrue(
            parsed_url.path.strip("/"),
            "DATABASE_URL debe incluir un nombre de base de datos.",
        )

        with (
            psycopg.connect(database_url, connect_timeout=5) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone(), (1,))
