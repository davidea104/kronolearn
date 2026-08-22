"""Learning persistence contracts."""

import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models import Q

from catalog.models import ImmutableModel


class Enrollment(models.Model):
    """Unique account enrollment in one track."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    track = models.ForeignKey(
        "catalog.Track", on_delete=models.PROTECT, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=9,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ("enrolled_at", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("account", "track"),
                name="learning_enrollment_account_track_unique",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("account", "status", "enrolled_at"),
                name="learn_enroll_account_idx",
            ),
        ]


class Attempt(ImmutableModel):
    """Append-only answer against an exact content snapshot."""

    class Rating(models.TextChoices):
        OPTIMAL = "OPTIMAL", "Optimal"
        PARTIAL = "PARTIAL", "Partially adequate"
        INCORRECT = "INCORRECT", "Incorrect"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.PROTECT, related_name="attempts"
    )
    content_version = models.ForeignKey(
        "catalog.ContentVersion",
        on_delete=models.PROTECT,
        related_name="attempts",
    )
    choice = models.ForeignKey(
        "catalog.Choice", on_delete=models.PROTECT, related_name="attempts"
    )
    rating = models.CharField(max_length=9, choices=Rating.choices)
    attempted_at = models.DateTimeField(auto_now_add=True)
    is_first_scoreable = models.BooleanField(default=False)
    idempotency_digest = models.CharField(max_length=64, unique=True, editable=False)

    class Meta:
        default_permissions = ("view",)
        ordering = ("attempted_at", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("enrollment", "content_version"),
                condition=Q(is_first_scoreable=True),
                name="learning_attempt_first_scoreable_unique",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("enrollment", "attempted_at"),
                name="learn_attempt_enrolled_idx",
            ),
        ]


class Progress(models.Model):
    """Replaceable progress aggregate for one enrollment and module."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.PROTECT, related_name="module_progress"
    )
    module = models.ForeignKey(
        "catalog.Module",
        on_delete=models.PROTECT,
        related_name="enrollment_progress",
    )
    completed_items = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("module__position", "module_id", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("enrollment", "module"),
                name="learning_progress_enrollment_module_unique",
            ),
            models.CheckConstraint(
                condition=Q(completed_items__lte=models.F("total_items")),
                name="learning_progress_completed_lte_total",
            ),
        ]
