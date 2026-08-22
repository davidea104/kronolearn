"""Migration contracts for catalog content."""

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ContentVersionEditorialStatusMigrationTests(TransactionTestCase):
    migrate_from = ("catalog", "0002_domain_content")
    migrate_to = ("catalog", "0003_contentversion_editorial_status")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps

        account_class = old_apps.get_model("accounts", "Account")
        track_class = old_apps.get_model("catalog", "Track")
        module_class = old_apps.get_model("catalog", "Module")
        content_item_class = old_apps.get_model("catalog", "ContentItem")
        content_version_class = old_apps.get_model("catalog", "ContentVersion")

        author = account_class.objects.create(
            email="migration-author@example.com",
            display_name="Migration Author",
            password="unusable",
        )
        track = track_class.objects.create(
            title="Track",
            title_key="track",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = module_class.objects.create(
            track=track,
            title="Modulo",
            title_key="modulo",
            objective="Objetivo",
            position=1,
        )
        content_item = content_item_class.objects.create(
            module=module,
            position=1,
        )
        self.version_id = content_version_class.objects.create(
            content_item=content_item,
            version_number=1,
            title="Unidad historica",
            learning_objective="Objetivo",
            lesson_text="Leccion",
            case_prompt="Caso",
            source="DOC-MIGRATION-001",
            author=author,
            reviewed_on="2026-08-22",
        ).pk

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_versions_are_backfilled_and_constraint_is_enforced(self):
        content_version_class = self.apps.get_model("catalog", "ContentVersion")
        content_version = content_version_class.objects.get(pk=self.version_id)

        self.assertEqual(content_version.editorial_status, "PUBLISHED")
        with self.assertRaises(IntegrityError), transaction.atomic():
            content_version_class.objects.filter(pk=self.version_id).update(
                editorial_status="DRAFT"
            )
