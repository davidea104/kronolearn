"""Administrative catalog web contracts."""

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE, LEARNER_ROLE
from catalog.models import CatalogChangeLog, CatalogState, Module, Track


class TrackAdminViewTests(TestCase):
    def setUp(self):
        self.admin_user = Account.objects.create_user(
            email="admin@example.com",
            display_name="Admin",
            password="Strong-test-password-123",
        )
        self.learner = Account.objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password="Strong-test-password-123",
        )
        content_group, _ = Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        learner_group, _ = Group.objects.get_or_create(name=LEARNER_ROLE)
        self.admin_user.groups.add(content_group)
        self.learner.groups.add(learner_group)

    def test_track_list_requires_content_admin_role(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("catalog:manage-track-list"))
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, "revision", status_code=403)

        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("catalog:manage-track-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tracks")

    def test_create_track_uses_prg_and_ignores_protected_fields(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("catalog:manage-track-create"),
            {
                "title": "Fundamentos",
                "description": "Descripcion",
                "audience": "Equipo",
                "status": "ACTIVE",
                "position": "99",
                "revision": "55",
            },
        )
        track = Track.objects.get()
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], reverse("catalog:manage-track-list"))
        self.assertEqual(track.status, Track.Status.INACTIVE)
        self.assertEqual((track.position, track.revision), (1, 1))

    def test_mutation_without_csrf_stops_before_service(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin_user)
        response = client.post(
            reverse("catalog:manage-track-create"),
            {"title": "Track", "description": "Desc", "audience": "Equipo"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Track.objects.exists())
        self.assertFalse(CatalogChangeLog.objects.exists())

    def test_state_and_reorder_routes_reject_get(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        routes = (
            reverse(
                "catalog:manage-track-activate",
                kwargs={"track_ref": str(track.pk)},
            ),
            reverse(
                "catalog:manage-track-deactivate",
                kwargs={"track_ref": str(track.pk)},
            ),
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(track.pk)},
            ),
            reverse(
                "catalog:manage-module-activate",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            reverse(
                "catalog:manage-module-deactivate",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
        )

        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 405)

        self.assertFalse(CatalogChangeLog.objects.exists())

    def test_malformed_track_reference_is_generic_and_audited(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-activate",
                kwargs={"track_ref": "not-a-uuid"},
            ),
            {"expected_revision": "1"},
        )
        log = CatalogChangeLog.objects.get()
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "not-a-uuid", status_code=404)
        self.assertEqual(log.result, CatalogChangeLog.Result.NOT_FOUND)
        self.assertEqual(len(log.unresolved_reference_digest), 64)

    def test_stale_state_request_returns_conflict_even_when_state_matches(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
            status=Track.Status.ACTIVE,
            published_version=1,
            revision=2,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-activate",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"expected_revision": "1"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(track.versions.count(), 0)

    def test_htmx_reorder_returns_only_allowlisted_rows(self):
        tracks = [
            Track.objects.create(
                title=f"Track {position}",
                description="Descripcion",
                audience="Equipo",
                position=position,
            )
            for position in range(1, 3)
        ]
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(tracks[1].pk)},
            ),
            {"position": "1", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="track-rows",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/partials/track_rows.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'role="status"')
        self.assertEqual(CatalogState.objects.get().track_order_revision, 1)

    def test_admin_page_loads_pinned_htmx_client(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("catalog:manage-track-list"))

        self.assertContains(
            response,
            (
                '<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/'
                'dist/htmx.min.js" integrity="sha384-ZBXiYtYQ6hJ2Y0ZNoYuI+'
                'Nq5MqWBr+chMrS/RkXpNzQCApHEhOt2aY8EJgqwHLkJ" '
                'crossorigin="anonymous" defer></script>'
            ),
            html=True,
        )
        self.assertContains(response, '"code":"409","swap":true,"error":false')

    def test_track_reorder_form_targets_allowlisted_rows(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        reorder_url = reverse(
            "catalog:manage-track-reorder",
            kwargs={"track_ref": str(track.pk)},
        )

        response = self.client.get(reverse("catalog:manage-track-list"))

        self.assertContains(
            response,
            (
                f'<form method="post" action="{reorder_url}" '
                f'hx-post="{reorder_url}" hx-target="#track-rows" '
                'hx-swap="innerHTML">'
            ),
        )

    def test_htmx_invalid_track_reorder_returns_rows_with_errors(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"position": "0", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="track-rows",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/partials/track_rows.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'role="alert"')

    def test_htmx_stale_track_reorder_returns_conflict_rows(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"position": "1", "expected_order_revision": "99"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="track-rows",
        )

        self.assertEqual(response.status_code, 409)
        self.assertTemplateUsed(response, "catalog/partials/track_rows.html")
        self.assertNotContains(response, "<html", status_code=409)
        self.assertContains(response, 'role="alert"', status_code=409)
        self.assertContains(
            response,
            'name="expected_order_revision" value="0"',
            status_code=409,
        )

        retry = self.client.post(
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"position": "1", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="track-rows",
        )
        self.assertEqual(retry.status_code, 200)

    def test_track_activation_requires_active_module_and_metadata(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
            status=Module.Status.ACTIVE,
            published_version=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-activate",
                kwargs={"track_ref": str(track.pk)},
            ),
            {
                "expected_revision": "1",
                "source": "DOC-001",
                "reviewed_on": "2026-08-21",
                "editorial_status": "APPROVED",
            },
        )
        self.assertEqual(response.status_code, 303)
        track.refresh_from_db()
        self.assertEqual(track.status, Track.Status.ACTIVE)
        self.assertEqual(track.versions.count(), 1)

    def test_module_create_uses_parent_from_url_and_prg(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        other = Track.objects.create(
            title="Otra",
            description="Descripcion",
            audience="Equipo",
            position=2,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-module-create",
                kwargs={"track_ref": str(track.pk)},
            ),
            {
                "title": "Modulo",
                "objective": "Objetivo",
                "track": str(other.pk),
                "position": "99",
                "status": "ACTIVE",
            },
        )
        module = Module.objects.get()
        self.assertEqual(response.status_code, 303)
        self.assertEqual(module.track_id, track.pk)
        self.assertEqual((module.position, module.status), (1, Module.Status.INACTIVE))

    def test_module_parent_mismatch_returns_generic_not_found_and_audit(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        other = Track.objects.create(
            title="Otra",
            description="Descripcion",
            audience="Equipo",
            position=2,
        )
        module = Module.objects.create(
            track=other,
            title="Ajeno",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-module-deactivate",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {"expected_revision": "1"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, str(module.pk), status_code=404)
        self.assertEqual(
            CatalogChangeLog.objects.get().result, CatalogChangeLog.Result.NOT_FOUND
        )

    def test_htmx_module_reorder_returns_allowlisted_rows(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        modules = [
            Module.objects.create(
                track=track,
                title=f"Modulo {position}",
                objective="Objetivo",
                position=position,
            )
            for position in range(1, 3)
        ]
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(modules[1].pk)},
            ),
            {"position": "1", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="module-rows",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/partials/module_rows.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'role="status"')

    def test_module_reorder_form_targets_allowlisted_rows(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        reorder_url = reverse(
            "catalog:manage-module-reorder",
            kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
        )

        response = self.client.get(
            reverse(
                "catalog:manage-module-list",
                kwargs={"track_ref": str(track.pk)},
            )
        )

        self.assertContains(
            response,
            (
                f'<form method="post" action="{reorder_url}" '
                f'hx-post="{reorder_url}" hx-target="#module-rows" '
                'hx-swap="innerHTML">'
            ),
        )

    def test_htmx_invalid_module_reorder_returns_rows_with_errors(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {"position": "0", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="module-rows",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/partials/module_rows.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'role="alert"')

    def test_htmx_stale_module_reorder_returns_conflict_rows(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {"position": "1", "expected_order_revision": "99"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="module-rows",
        )

        self.assertEqual(response.status_code, 409)
        self.assertTemplateUsed(response, "catalog/partials/module_rows.html")
        self.assertNotContains(response, "<html", status_code=409)
        self.assertContains(response, 'role="alert"', status_code=409)
        self.assertContains(
            response,
            'name="expected_order_revision" value="0"',
            status_code=409,
        )

        retry = self.client.post(
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {"position": "1", "expected_order_revision": "0"},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="module-rows",
        )
        self.assertEqual(retry.status_code, 200)

    def test_learner_post_reaching_service_is_denied_once_without_disclosure(self):
        track = Track.objects.create(
            title="Ruta privada",
            description="Descripcion privada",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse(
                "catalog:manage-module-create",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"title": "No permitido", "objective": "No permitido"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, "Ruta privada", status_code=403)
        self.assertFalse(Module.objects.exists())
        log = CatalogChangeLog.objects.get()
        self.assertEqual(log.result, CatalogChangeLog.Result.DENIED)
        self.assertFalse(log.changed)

    def test_invalid_track_form_has_accessible_error_summary(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("catalog:manage-track-create"),
            {"title": " ", "description": "", "audience": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="error-summary"')
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, "Revisa los datos ingresados")

    def test_unknown_htmx_target_does_not_select_arbitrary_template(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("catalog:manage-track-list"),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="../../private-template",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/manage_track_list.html")
        self.assertContains(response, "<html")

    def test_non_numeric_track_reorder_is_invalid_not_conflict(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-reorder",
                kwargs={"track_ref": str(track.pk)},
            ),
            {"position": "not-a-number", "expected_order_revision": "0"},
        )
        self.assertEqual(response.status_code, 200)
        log = CatalogChangeLog.objects.get()
        self.assertEqual(log.result, CatalogChangeLog.Result.INVALID)

    def test_non_numeric_module_reorder_is_invalid_not_conflict(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-module-reorder",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {"position": "not-a-number", "expected_order_revision": "0"},
        )
        self.assertEqual(response.status_code, 200)
        log = CatalogChangeLog.objects.get()
        self.assertEqual(log.result, CatalogChangeLog.Result.INVALID)

    def test_non_numeric_track_revision_is_invalid_not_conflict(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-track-edit",
                kwargs={"track_ref": str(track.pk)},
            ),
            {
                "title": "Ruta editada",
                "description": "Descripcion",
                "audience": "Equipo",
                "expected_revision": "not-a-number",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            CatalogChangeLog.objects.get().result, CatalogChangeLog.Result.INVALID
        )

    def test_non_numeric_module_revision_is_invalid_not_conflict(self):
        track = Track.objects.create(
            title="Ruta",
            description="Descripcion",
            audience="Equipo",
            position=1,
        )
        module = Module.objects.create(
            track=track,
            title="Modulo",
            objective="Objetivo",
            position=1,
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse(
                "catalog:manage-module-edit",
                kwargs={"track_ref": str(track.pk), "module_ref": str(module.pk)},
            ),
            {
                "title": "Modulo editado",
                "objective": "Objetivo",
                "expected_revision": "not-a-number",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            CatalogChangeLog.objects.get().result, CatalogChangeLog.Result.INVALID
        )
