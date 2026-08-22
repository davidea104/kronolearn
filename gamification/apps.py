"""Django application configuration for gamification."""

from django.apps import AppConfig


class GamificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gamification"

    def ready(self):
        from gamification import receivers  # noqa: F401
