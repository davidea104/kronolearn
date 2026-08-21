"""Identity, throttling, and role-audit persistence."""

import uuid
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from accounts.managers import AccountManager
from accounts.security import canonicalize_account_email


class Account(AbstractUser):
    """Email-address identity used by all KronoLearn modules."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["display_name"]

    objects = AccountManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_account_email_ci_unique",
            )
        ]

    def clean(self):
        super().clean()
        self.email = canonicalize_account_email(self.email)

    def save(self, *args, **kwargs):
        self.email = canonicalize_account_email(self.email)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class LoginThrottleBucket(models.Model):
    """Shared progressive-login delay state keyed by pseudonymous references."""

    class Scope(models.TextChoices):
        ACCOUNT = "ACCOUNT", "Account"
        ORIGIN = "ORIGIN", "Origin"

    scope = models.CharField(max_length=16, choices=Scope.choices)
    key_digest = models.CharField(max_length=64)
    failure_count = models.PositiveIntegerField()
    last_failed_at = models.DateTimeField()
    blocked_until = models.DateTimeField()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("scope", "key_digest"),
                name="accounts_throttle_scope_digest_unique",
            ),
            models.CheckConstraint(
                condition=Q(failure_count__gte=1),
                name="accounts_throttle_failure_count_positive",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("scope", "blocked_until"),
                name="acct_thr_scope_block_idx",
            ),
            models.Index(
                fields=("last_failed_at",),
                name="acct_thr_failed_idx",
            ),
        ]


class RoleChangeLog(models.Model):
    """Immutable evidence for every authenticated content-role attempt."""

    class Action(models.TextChoices):
        ASSIGN = "ASSIGN", "Assign"
        REVOKE = "REVOKE", "Revoke"

    class Result(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        DENIED = "DENIED", "Denied"
        TARGET_NOT_FOUND = "TARGET_NOT_FOUND", "Target not found"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="role_changes_performed",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="role_changes_received",
    )
    requested_target_digest = models.CharField(max_length=64, null=True, blank=True)
    action = models.CharField(max_length=8, choices=Action.choices)
    result = models.CharField(max_length=20, choices=Result.choices)
    changed = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=(
                    Q(target__isnull=False, requested_target_digest__isnull=True)
                    | Q(target__isnull=True, requested_target_digest__isnull=False)
                ),
                name="accounts_role_target_xor_digest",
            ),
            models.CheckConstraint(
                condition=(
                    Q(result="TARGET_NOT_FOUND", target__isnull=True)
                    | (~Q(result="TARGET_NOT_FOUND") & Q(target__isnull=False))
                ),
                name="accounts_role_not_found_iff_target_null",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(result__in=("DENIED", "TARGET_NOT_FOUND")) | Q(changed=False)
                ),
                name="accounts_role_failed_never_changed",
            ),
            models.CheckConstraint(
                condition=(
                    Q(changed=False) | Q(result="SUCCESS", target__isnull=False)
                ),
                name="accounts_role_changed_requires_success",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("target", "occurred_at"),
                name="acct_role_target_time_idx",
            ),
            models.Index(
                fields=("requested_target_digest", "occurred_at"),
                name="acct_role_digest_time_idx",
            ),
            models.Index(
                fields=("actor", "occurred_at"),
                name="acct_role_actor_time_idx",
            ),
            models.Index(
                fields=("result", "occurred_at"),
                name="acct_role_result_time_idx",
            ),
        ]
