"""Django application configuration for learning."""

from django.apps import AppConfig


class LearningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "learning"

    def ready(self):
        from learning import receivers  # noqa: F401
