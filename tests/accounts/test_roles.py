"""Transactional content-role service contracts."""

import importlib
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import RoleChangeLog
from accounts.security import CONTENT_ADMIN_ROLE, LEARNER_ROLE, security_digest

VALID_PASSWORD = "correct-horse-battery-staple"


class ContentRoleServiceTests(TransactionTestCase):
    def setUp(self):
        account_class = get_user_model()
        learner_group, _ = Group.objects.get_or_create(name=LEARNER_ROLE)
        Group.objects.get_or_create(name=CONTENT_ADMIN_ROLE)
        self.admin = account_class.objects.create_superuser(
            email="admin@example.com",
            display_name="Platform Admin",
            password=VALID_PASSWORD,
        )
        self.learner = account_class.objects.create_user(
            email="learner@example.com",
            display_name="Learner",
            password=VALID_PASSWORD,
        )
        self.other = account_class.objects.create_user(
            email="other@example.com",
            display_name="Other Learner",
            password=VALID_PASSWORD,
        )
        self.learner.groups.add(learner_group)
        self.other.groups.add(learner_group)

    def service(self):
        try:
            return importlib.import_module("accounts.services.roles")
        except ModuleNotFoundError as exc:
            self.fail(f"Role service is missing: {exc.name}")

    def backend_waits_for_lock(self, backend_pid, future):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if future.done():
                return False
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s",
                    [backend_pid],
                )
                row = cursor.fetchone()
            if row and row[0] == "Lock":
                return True
            time.sleep(0.02)
        return False

    def test_assign_and_revoke_are_successful_idempotent_and_preserve_learner(self):
        service = self.service()

        assigned = service.change_content_role(
            self.admin, str(self.learner.pk), RoleChangeLog.Action.ASSIGN
        )
        repeated = service.change_content_role(
            self.admin, str(self.learner.pk), RoleChangeLog.Action.ASSIGN
        )
        revoked = service.change_content_role(
            self.admin, str(self.learner.pk), RoleChangeLog.Action.REVOKE
        )
        repeated_revoke = service.change_content_role(
            self.admin, str(self.learner.pk), RoleChangeLog.Action.REVOKE
        )

        self.assertEqual(
            [
                assigned.changed,
                repeated.changed,
                revoked.changed,
                repeated_revoke.changed,
            ],
            [True, False, True, False],
        )
        self.assertTrue(self.learner.groups.filter(name=LEARNER_ROLE).exists())
        self.assertFalse(self.learner.groups.filter(name=CONTENT_ADMIN_ROLE).exists())
        self.assertEqual(
            list(RoleChangeLog.objects.values_list("result", "changed")),
            [
                (RoleChangeLog.Result.SUCCESS, True),
                (RoleChangeLog.Result.SUCCESS, False),
                (RoleChangeLog.Result.SUCCESS, True),
                (RoleChangeLog.Result.SUCCESS, False),
            ],
        )

    def test_unauthorized_actor_and_self_target_are_denied_once(self):
        service = self.service()

        unauthorized = service.change_content_role(
            self.learner, str(self.other.pk), RoleChangeLog.Action.ASSIGN
        )
        self_target = service.change_content_role(
            self.admin, str(self.admin.pk), RoleChangeLog.Action.REVOKE
        )

        self.assertEqual(unauthorized.result, RoleChangeLog.Result.DENIED)
        self.assertEqual(self_target.result, RoleChangeLog.Result.DENIED)
        self.assertFalse(unauthorized.changed)
        self.assertFalse(self_target.changed)
        self.assertFalse(self.other.groups.filter(name=CONTENT_ADMIN_ROLE).exists())
        logs = list(RoleChangeLog.objects.order_by("occurred_at"))
        self.assertEqual(len(logs), 2)
        self.assertEqual([log.target for log in logs], [self.other, self.admin])
        self.assertTrue(all(log.requested_target_digest is None for log in logs))

    def test_nonexistent_uuid_uses_canonical_digest_and_no_target(self):
        service = self.service()
        missing_id = uuid.uuid4()

        outcome = service.change_content_role(
            self.admin,
            str(missing_id).upper(),
            RoleChangeLog.Action.ASSIGN,
        )

        log = RoleChangeLog.objects.get()
        self.assertEqual(outcome.result, RoleChangeLog.Result.TARGET_NOT_FOUND)
        self.assertFalse(outcome.changed)
        self.assertIsNone(log.target)
        self.assertEqual(
            log.requested_target_digest,
            security_digest(str(missing_id), purpose="role-target"),
        )
        self.assertNotIn(str(missing_id), log.requested_target_digest)

    def test_malformed_reference_uses_raw_segment_digest_without_storing_segment(self):
        service = self.service()
        malformed = "not-a-uuid"

        outcome = service.change_content_role(
            self.learner,
            malformed,
            RoleChangeLog.Action.REVOKE,
        )

        log = RoleChangeLog.objects.get()
        self.assertEqual(outcome.result, RoleChangeLog.Result.TARGET_NOT_FOUND)
        self.assertEqual(
            log.requested_target_digest,
            security_digest(malformed, purpose="role-target"),
        )
        self.assertNotIn(malformed, str(log.__dict__))
        self.assertIsNone(log.target)

    def test_unresolved_targets_use_current_actor_authority(self):
        service = self.service()
        get_user_model().objects.filter(pk=self.admin.pk).update(is_superuser=False)

        outcomes = [
            service.change_content_role(
                self.admin,
                target_ref,
                RoleChangeLog.Action.ASSIGN,
            )
            for target_ref in (str(uuid.uuid4()), "not-a-uuid")
        ]

        self.assertTrue(
            all(
                not getattr(outcome, "actor_is_platform_admin", True)
                for outcome in outcomes
            )
        )
        self.assertEqual(RoleChangeLog.objects.count(), 2)
        self.assertTrue(
            all(
                result == RoleChangeLog.Result.TARGET_NOT_FOUND
                for result in RoleChangeLog.objects.values_list("result", flat=True)
            )
        )

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_authority_revocation_precedes_role_decision(self):
        service = self.service()
        authority_locked = threading.Event()
        release_authority_lock = threading.Event()
        role_backend_pids = Queue()

        def revoke_authority():
            connections.close_all()
            try:
                with transaction.atomic():
                    current_admin = (
                        get_user_model()
                        .objects.select_for_update()
                        .get(pk=self.admin.pk)
                    )
                    current_admin.is_superuser = False
                    current_admin.save(update_fields=("is_superuser",))
                    authority_locked.set()
                    if not release_authority_lock.wait(timeout=5):
                        raise AssertionError(
                            "Role attempt did not reach the actor lock."
                        )
            finally:
                connections.close_all()

        def assign_role():
            connections.close_all()
            try:
                current_connection = connections["default"]
                with current_connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    role_backend_pids.put(cursor.fetchone()[0])
                return service.change_content_role(
                    self.admin,
                    str(self.other.pk),
                    RoleChangeLog.Action.ASSIGN,
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            revoke_future = executor.submit(revoke_authority)
            self.assertTrue(authority_locked.wait(timeout=5))
            role_future = executor.submit(assign_role)
            role_backend_pid = role_backend_pids.get(timeout=5)
            try:
                self.assertTrue(
                    self.backend_waits_for_lock(role_backend_pid, role_future)
                )
            finally:
                release_authority_lock.set()
            revoke_future.result()
            outcome = role_future.result()

        self.assertEqual(outcome.result, RoleChangeLog.Result.DENIED)
        self.assertFalse(outcome.actor_is_platform_admin)
        self.assertFalse(self.other.groups.filter(name=CONTENT_ADMIN_ROLE).exists())
        log = RoleChangeLog.objects.get()
        self.assertEqual(log.result, RoleChangeLog.Result.DENIED)
        self.assertFalse(log.changed)

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_assignments_lock_target_and_audit_both_attempts(self):
        service = self.service()
        barrier = threading.Barrier(2)

        def assign_role():
            connections.close_all()
            actor = get_user_model().objects.get(pk=self.admin.pk)
            barrier.wait()
            try:
                return service.change_content_role(
                    actor,
                    str(self.other.pk),
                    RoleChangeLog.Action.ASSIGN,
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(assign_role) for _ in range(2)]
            for future in futures:
                future.result()

        self.assertEqual(connection.vendor, "postgresql")
        self.assertEqual(RoleChangeLog.objects.count(), 2)
        self.assertEqual(
            sorted(RoleChangeLog.objects.values_list("changed", flat=True)),
            [False, True],
        )
        self.assertEqual(
            self.other.groups.filter(name=CONTENT_ADMIN_ROLE).count(),
            1,
        )
