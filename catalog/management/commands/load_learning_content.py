"""Load the approved learning-content corpus during deployment."""

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from catalog.content_data import load_definitions
from catalog.services.content import ContentLoadConflict, load_learning_content


class Command(BaseCommand):
    help = "Load and reconcile the approved learning content."

    def handle(self, *args, **options):
        actor_ref = settings.CONTENT_AUTHOR_ACCOUNT_ID
        if not actor_ref:
            raise CommandError("Learning-content author configuration is required.")

        try:
            definitions = load_definitions()
            outcome = load_learning_content(actor_ref, definitions)
        except PermissionDenied:
            raise CommandError("Learning-content author is not authorized.") from None
        except (ValidationError, ValueError):
            raise CommandError("Learning-content definition is invalid.") from None
        except ContentLoadConflict:
            raise CommandError("Learning-content reconciliation conflict.") from None
        self.stdout.write(
            self.style.SUCCESS(
                f"Contenido listo: {outcome.track_count} tracks, "
                f"{outcome.module_count} módulos, "
                f"{outcome.content_item_count} unidades; "
                f"{outcome.items_created} unidades creadas, "
                f"{outcome.versions_created} versiones creadas."
            )
        )
