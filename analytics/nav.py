"""Analytics-owned reserved navigation declarations."""

from accounts.security import CONTENT_ADMIN_ROLE
from ui.navigation import NavItem

NAV_ITEMS = (
    NavItem(
        "content-metrics",
        "Métricas",
        "analytics:content-metrics",
        60,
        required_role=CONTENT_ADMIN_ROLE,
    ),
)
