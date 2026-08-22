"""Distributed, authorization-aware primary navigation discovery."""

from dataclasses import dataclass
from importlib import import_module

from django.apps import apps
from django.core.checks import Error, Tags, register
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, reverse


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    url_name: str
    order: int
    authenticated: bool = True
    required_role: str | None = None
    superuser_only: bool = False


@dataclass(frozen=True)
class ResolvedNavItem:
    key: str
    label: str
    url: str
    order: int


def _declared_items() -> tuple[NavItem, ...]:
    items = []
    seen = set()
    for app_config in apps.get_app_configs():
        module_name = f"{app_config.name}.nav"
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name or module_name.startswith(f"{error.name}."):
                continue
            raise
        for item in getattr(module, "NAV_ITEMS", ()):
            if item.key in seen:
                raise ImproperlyConfigured(f"Duplicate navigation key: {item.key}")
            seen.add(item.key)
            items.append(item)
    return tuple(items)


def _is_allowed(item: NavItem, account) -> bool:
    is_authenticated = bool(
        account is not None and getattr(account, "is_authenticated", False)
    )
    if item.authenticated and not is_authenticated:
        return False
    if item.superuser_only and not (
        is_authenticated and getattr(account, "is_superuser", False)
    ):
        return False
    return not item.required_role or bool(
        is_authenticated and account.groups.filter(name=item.required_role).exists()
    )


def primary_navigation(account=None) -> tuple[ResolvedNavItem, ...]:
    """Resolve visible entries from optional app declarations in stable order."""
    resolved = []
    for item in _declared_items():
        if not _is_allowed(item, account):
            continue
        try:
            url = reverse(item.url_name)
        except NoReverseMatch:
            continue
        resolved.append(ResolvedNavItem(item.key, item.label, url, item.order))
    return tuple(sorted(resolved, key=lambda item: (item.order, item.key)))


@register(Tags.urls)
def check_navigation_keys(app_configs, **kwargs):
    try:
        _declared_items()
    except ImproperlyConfigured as error:
        return [Error(str(error), id="ui.E001")]
    return []
