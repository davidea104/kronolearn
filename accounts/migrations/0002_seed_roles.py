"""Seed the canonical cumulative account roles."""

from typing import ClassVar

from django.db import migrations

ROLE_NAMES = ("learner", "content_admin")


def seed_roles(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    manager = group.objects.using(schema_editor.connection.alias)
    for role_name in ROLE_NAMES:
        manager.get_or_create(name=role_name)


def unseed_roles(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.using(schema_editor.connection.alias).filter(
        name__in=ROLE_NAMES
    ).delete()


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [
        ("accounts", "0001_initial"),
    ]

    operations: ClassVar[list[object]] = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
