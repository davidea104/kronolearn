"""Shared template context for app-distributed navigation."""

from ui.navigation import primary_navigation as resolve_primary_navigation


def primary_navigation(request):
    return {"primary_navigation": resolve_primary_navigation(request.user)}
