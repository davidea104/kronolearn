"""Account-owned primary navigation declarations."""

from ui.navigation import NavItem

NAV_ITEMS = (
    NavItem("account-profile", "Perfil", "accounts:profile", 80),
    NavItem(
        "account-roles",
        "Roles",
        "accounts:role-management",
        90,
        superuser_only=True,
    ),
)
