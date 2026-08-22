"""Catalog-owned primary navigation declarations."""

from accounts.security import CONTENT_ADMIN_ROLE
from ui.navigation import NavItem

NAV_ITEMS = (
    NavItem("catalog", "Catálogo", "catalog:track-list", 20),
    NavItem(
        "catalog-manage",
        "Gestionar catálogo",
        "catalog:manage-track-list",
        70,
        required_role=CONTENT_ADMIN_ROLE,
    ),
)
