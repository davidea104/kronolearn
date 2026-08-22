"""Create the deterministic minimal KronoLearn demonstration graph."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE, LEARNER_ROLE
from catalog.models import (
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
)
from gamification.services.seasons import current_season

DEMO_ACCOUNTS = (
    ("learner@demo.kronolearn.invalid", "Aprendiz Demo", LEARNER_ROLE),
    (
        "content-admin@demo.kronolearn.invalid",
        "Administración Demo",
        CONTENT_ADMIN_ROLE,
    ),
)

DEMO_TRACKS = (
    {
        "title": "Crea tu registro de gastos con agentes y SDD",
        "description": "Construye un registro de gastos asistido y verificable.",
        "audience": "Personas que aprenden desarrollo asistido",
        "module_title": "Diseña el registro",
        "module_objective": "Definir y validar un flujo mínimo de gastos.",
        "content_title": "Del requisito al registro",
    },
    {
        "title": "Fundamentos de negocio para equipos técnicos",
        "description": "Conecta decisiones técnicas con resultados de negocio.",
        "audience": "Equipos técnicos",
        "module_title": "Habla el lenguaje del negocio",
        "module_objective": "Relacionar métricas técnicas y resultados.",
        "content_title": "Decisiones con contexto",
    },
)


class Command(BaseCommand):
    help = "Create or repair the deterministic KronoLearn demo data."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-production", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["confirm_production"]:
            raise CommandError(
                "Refusing to seed demo data without --confirm-production."
            )
        with transaction.atomic():
            accounts = self._accounts()
            tracks = [
                self._track(definition, accounts[CONTENT_ADMIN_ROLE])
                for definition in DEMO_TRACKS
            ]
            current_season(timezone.now())
        titles = ", ".join(track.title for track in tracks)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {len(accounts)} accounts, {len(tracks)} tracks: {titles}"
            )
        )

    def _accounts(self):
        accounts = {}
        for email, display_name, role_name in DEMO_ACCOUNTS:
            account, created = Account.objects.get_or_create(
                email=email,
                defaults={"display_name": display_name, "is_active": True},
            )
            if created or (not settings.DEBUG and account.has_usable_password()):
                account.set_unusable_password()
                account.save(update_fields=("password",))
            group, _ = Group.objects.get_or_create(name=role_name)
            account.groups.add(group)
            accounts[role_name] = account
        return accounts

    def _track(self, definition, author):
        track = Track.objects.filter(title_key=definition["title"].casefold()).first()
        if track is None:
            position = (
                Track.objects.aggregate(value=Max("position"))["value"] or 0
            ) + 1
            track = Track.objects.create(
                title=definition["title"],
                description=definition["description"],
                audience=definition["audience"],
                position=position,
                status=Track.Status.ACTIVE,
                published_version=1,
            )
        else:
            update_fields = []
            if track.status != Track.Status.ACTIVE:
                track.status = Track.Status.ACTIVE
                update_fields.append("status")
            if track.published_version < 1:
                track.published_version = 1
                update_fields.append("published_version")
            if update_fields:
                track.save(update_fields=(*update_fields, "updated_at"))
        TrackVersion.objects.get_or_create(
            track=track,
            version_number=1,
            defaults={
                "title": track.title,
                "description": track.description,
                "audience": track.audience,
                "author": author,
                "source": "KronoLearn demo",
                "reviewed_on": timezone.localdate(),
                "editorial_status": TrackVersion.EditorialStatus.APPROVED,
            },
        )
        self._module(track, definition, author)
        return track

    def _module(self, track, definition, author):
        title = definition["module_title"]
        module = Module.objects.filter(track=track, title_key=title.casefold()).first()
        if module is None:
            position = (
                track.modules.aggregate(value=Max("position"))["value"] or 0
            ) + 1
            module = Module.objects.create(
                track=track,
                title=title,
                objective=definition["module_objective"],
                position=position,
                status=Module.Status.ACTIVE,
                published_version=1,
            )
        else:
            update_fields = []
            if module.status != Module.Status.ACTIVE:
                module.status = Module.Status.ACTIVE
                update_fields.append("status")
            if module.published_version < 1:
                module.published_version = 1
                update_fields.append("published_version")
            if update_fields:
                module.save(update_fields=(*update_fields, "updated_at"))
        ModuleVersion.objects.get_or_create(
            module=module,
            version_number=1,
            defaults={
                "title": module.title,
                "objective": module.objective,
                "author": author,
                "source": "KronoLearn demo",
                "reviewed_on": timezone.localdate(),
                "editorial_status": ModuleVersion.EditorialStatus.APPROVED,
            },
        )
        self._content(module, definition, author)

    def _content(self, module, definition, author):
        item, _ = ContentItem.objects.get_or_create(
            module=module,
            position=1,
            defaults={
                "status": ContentItem.Status.PUBLISHED,
                "published_version": 1,
            },
        )
        update_fields = []
        if item.status != ContentItem.Status.PUBLISHED:
            item.status = ContentItem.Status.PUBLISHED
            update_fields.append("status")
        if item.published_version < 1:
            item.published_version = 1
            update_fields.append("published_version")
        if update_fields:
            item.save(update_fields=(*update_fields, "updated_at"))
        version, _ = ContentVersion.objects.get_or_create(
            content_item=item,
            version_number=1,
            defaults={
                "title": definition["content_title"],
                "learning_objective": definition["module_objective"],
                "lesson_text": "Analiza el contexto y registra una decisión verificable.",
                "case_prompt": "Elige la respuesta que mejor conecta evidencia y acción.",
                "source": "KronoLearn demo",
                "author": author,
                "reviewed_on": timezone.localdate(),
            },
        )
        choices = (
            (1, Choice.Rating.OPTIMAL),
            (2, Choice.Rating.PARTIAL),
            (3, Choice.Rating.INCORRECT),
        )
        for position, rating in choices:
            Choice.objects.get_or_create(
                content_version=version,
                position=position,
                defaults={
                    "text": f"Opción {position}",
                    "rating": rating,
                    "consequence": "La decisión produce un resultado observable.",
                    "explanation": "Compara la decisión con el objetivo del módulo.",
                },
            )
        LabExercise.objects.get_or_create(
            content_version=version,
            defaults={
                "objective": "Aplicar la decisión en un artefacto pequeño.",
                "initial_prompt": "Construye una primera versión verificable.",
                "expected_artifact": "Un artefacto ejecutable con evidencia.",
                "verification_checklist": [
                    "Ejecuta la verificación",
                    "Registra el resultado",
                ],
            },
        )
