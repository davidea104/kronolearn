"""Contract tests for distributed navigation discovery."""

import sys
from dataclasses import FrozenInstanceError
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.urls import NoReverseMatch

from ui.navigation import NavItem, primary_navigation


class _Groups:
    def __init__(self, names=()):
        self.names = set(names)

    def filter(self, *, name):
        return SimpleNamespace(exists=lambda: name in self.names)


class NavigationContractTests(SimpleTestCase):
    def _account(self, *, authenticated=True, roles=(), superuser=False):
        return SimpleNamespace(
            is_authenticated=authenticated,
            is_superuser=superuser,
            groups=_Groups(roles),
        )

    def test_nav_item_is_frozen(self):
        item = NavItem("home", "Home", "ui:learner-home", 10)
        with self.assertRaises(FrozenInstanceError):
            item.order = 20

    def test_discovery_filters_authorization_sorts_and_omits_unresolved(self):
        first = ModuleType("first.nav")
        first.NAV_ITEMS = (
            NavItem("z", "Z", "route:z", 20),
            NavItem("admin", "Admin", "route:admin", 10, required_role="admin"),
        )
        second = ModuleType("second.nav")
        second.NAV_ITEMS = (
            NavItem("a", "A", "route:a", 20),
            NavItem("future", "Future", "route:missing", 5),
            NavItem("root", "Root", "route:root", 1, superuser_only=True),
        )
        configs = (SimpleNamespace(name="first"), SimpleNamespace(name="second"))

        def reverse(url_name):
            if url_name == "route:missing":
                raise NoReverseMatch
            return f"/{url_name}/"

        with (
            patch.dict(sys.modules, {"first.nav": first, "second.nav": second}),
            patch("ui.navigation.apps.get_app_configs", return_value=configs),
            patch("ui.navigation.reverse", side_effect=reverse),
        ):
            entries = primary_navigation(self._account(roles=("admin",)))

        self.assertIsInstance(entries, tuple)
        self.assertEqual([entry.key for entry in entries], ["admin", "a", "z"])
        self.assertEqual(entries[0].url, "/route:admin/")

    def test_duplicate_keys_are_rejected(self):
        first = ModuleType("first.nav")
        first.NAV_ITEMS = (NavItem("same", "First", "route:first", 1),)
        second = ModuleType("second.nav")
        second.NAV_ITEMS = (NavItem("same", "Second", "route:second", 2),)
        configs = (SimpleNamespace(name="first"), SimpleNamespace(name="second"))
        with (
            patch.dict(sys.modules, {"first.nav": first, "second.nav": second}),
            patch("ui.navigation.apps.get_app_configs", return_value=configs),
            self.assertRaises(ImproperlyConfigured),
        ):
            primary_navigation(self._account())

    def test_optional_nav_module_is_ignored(self):
        configs = (SimpleNamespace(name="not_installed_for_test"),)
        with patch("ui.navigation.apps.get_app_configs", return_value=configs):
            self.assertEqual(primary_navigation(self._account()), ())
