"""Learning-owned reserved navigation declarations."""

from ui.navigation import NavItem

NAV_ITEMS = (
    NavItem("learning-enrollment", "Tracks", "learning:enrollment-list", 10),
    NavItem("learning-session", "Sesión", "learning:session-current", 30),
    NavItem("learning-progress", "Progreso", "learning:progress-detail", 40),
)
