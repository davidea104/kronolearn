"""Catalog content, immutable publication versions, and audit evidence."""

import uuid
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def canonicalize_title(value: str) -> str:
    return value.strip().casefold()


class ImmutableModel(models.Model):
    """Reject model-level changes to append-only records."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Published history is immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Published history is immutable.")


class CatalogState(models.Model):
    """Singleton lock row for the global track sequence."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    track_order_revision = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(condition=Q(id=1), name="catalog_state_singleton"),
        ]


class Track(models.Model):
    """Mutable learning route in the administrative catalog."""

    class Status(models.TextChoices):
        INACTIVE = "INACTIVE", "Inactive"
        ACTIVE = "ACTIVE", "Active"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=160)
    title_key = models.CharField(max_length=480, unique=True, editable=False)
    description = models.CharField(max_length=2000)
    audience = models.CharField(max_length=500)
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.INACTIVE,
    )
    position = models.PositiveIntegerField(unique=True)
    revision = models.PositiveBigIntegerField(default=1)
    module_order_revision = models.PositiveBigIntegerField(default=0)
    published_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("position", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(position__gte=1), name="catalog_track_position_positive"
            ),
            models.CheckConstraint(
                condition=Q(revision__gte=1), name="catalog_track_revision_positive"
            ),
            models.CheckConstraint(
                condition=Q(status="INACTIVE") | Q(published_version__gte=1),
                name="catalog_track_active_has_version",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("status", "position"), name="catalog_track_status_pos_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.title_key = canonicalize_title(self.title)
        return super().save(*args, **kwargs)


class Module(models.Model):
    """Mutable ordered learning unit owned by one track."""

    class Status(models.TextChoices):
        INACTIVE = "INACTIVE", "Inactive"
        ACTIVE = "ACTIVE", "Active"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    track = models.ForeignKey(Track, on_delete=models.PROTECT, related_name="modules")
    title = models.CharField(max_length=160)
    title_key = models.CharField(max_length=480, editable=False)
    objective = models.CharField(max_length=1000)
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.INACTIVE,
    )
    position = models.PositiveIntegerField()
    revision = models.PositiveBigIntegerField(default=1)
    published_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("track_id", "position", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("track", "title_key"), name="catalog_module_track_title_unique"
            ),
            models.UniqueConstraint(
                fields=("track", "position"),
                name="catalog_module_track_position_unique",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1), name="catalog_module_position_positive"
            ),
            models.CheckConstraint(
                condition=Q(revision__gte=1), name="catalog_module_revision_positive"
            ),
            models.CheckConstraint(
                condition=Q(status="INACTIVE") | Q(published_version__gte=1),
                name="catalog_module_active_has_version",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("track", "status", "position"),
                name="catalog_module_track_state_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.title_key = canonicalize_title(self.title)
        return super().save(*args, **kwargs)


class TrackVersion(ImmutableModel):
    """Append-only published snapshot of a track."""

    class EditorialStatus(models.TextChoices):
        APPROVED = "APPROVED", "Approved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    track = models.ForeignKey(Track, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=2000)
    audience = models.CharField(max_length=500)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="track_versions_authored",
    )
    source = models.CharField(max_length=500)
    reviewed_on = models.DateField()
    editorial_status = models.CharField(max_length=8, choices=EditorialStatus.choices)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("track", "version_number"), name="catalog_track_version_unique"
            ),
            models.CheckConstraint(
                condition=Q(version_number__gte=1),
                name="catalog_track_version_positive",
            ),
            models.CheckConstraint(
                condition=Q(editorial_status="APPROVED"),
                name="catalog_track_version_approved",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("track", "-version_number"), name="catalog_track_version_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        self.source = self.source.strip()
        return super().save(*args, **kwargs)


class ModuleVersion(ImmutableModel):
    """Append-only published snapshot of a module."""

    class EditorialStatus(models.TextChoices):
        APPROVED = "APPROVED", "Approved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        Module, on_delete=models.PROTECT, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    objective = models.CharField(max_length=1000)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="module_versions_authored",
    )
    source = models.CharField(max_length=500)
    reviewed_on = models.DateField()
    editorial_status = models.CharField(max_length=8, choices=EditorialStatus.choices)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("module", "version_number"),
                name="catalog_module_version_unique",
            ),
            models.CheckConstraint(
                condition=Q(version_number__gte=1),
                name="catalog_module_version_positive",
            ),
            models.CheckConstraint(
                condition=Q(editorial_status="APPROVED"),
                name="catalog_module_version_approved",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("module", "-version_number"), name="catalog_module_version_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        self.source = self.source.strip()
        return super().save(*args, **kwargs)


class ContentItem(models.Model):
    """Mutable ordered content unit owned by one module."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        Module, on_delete=models.PROTECT, related_name="content_items"
    )
    position = models.PositiveIntegerField()
    status = models.CharField(
        max_length=9,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    revision = models.PositiveBigIntegerField(default=1)
    published_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("module_id", "position", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("module", "position"),
                name="catalog_content_module_position_unique",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1),
                name="catalog_content_position_positive",
            ),
            models.CheckConstraint(
                condition=Q(revision__gte=1),
                name="catalog_content_revision_positive",
            ),
            models.CheckConstraint(
                condition=Q(status="DRAFT") | Q(published_version__gte=1),
                name="catalog_content_published_has_version",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("module", "status", "position"),
                name="catalog_content_state_idx",
            ),
        ]


class ContentVersion(ImmutableModel):
    """Append-only snapshot of learner-facing content."""

    class EditorialStatus(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_item = models.ForeignKey(
        ContentItem, on_delete=models.PROTECT, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    learning_objective = models.CharField(max_length=1000)
    lesson_text = models.TextField()
    case_prompt = models.TextField()
    source = models.CharField(max_length=500)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="content_versions_authored",
    )
    reviewed_on = models.DateField()
    editorial_status = models.CharField(
        max_length=9,
        choices=EditorialStatus.choices,
        default=EditorialStatus.PUBLISHED,
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("content_item", "version_number"),
                name="catalog_content_version_unique",
            ),
            models.CheckConstraint(
                condition=Q(version_number__gte=1),
                name="catalog_content_version_positive",
            ),
            models.CheckConstraint(
                condition=~Q(source=""),
                name="catalog_content_source_nonempty",
            ),
            models.CheckConstraint(
                condition=Q(editorial_status="PUBLISHED"),
                name="catalog_content_version_published",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("content_item", "-version_number"),
                name="catalog_content_version_idx",
            ),
        ]

    @property
    def is_current(self) -> bool:
        return self.version_number == self.content_item.published_version

    def save(self, *args, **kwargs):
        self.source = self.source.strip()
        return super().save(*args, **kwargs)


class Choice(ImmutableModel):
    """Append-only answer option for one content snapshot."""

    class Rating(models.TextChoices):
        OPTIMAL = "OPTIMAL", "Optimal"
        PARTIAL = "PARTIAL", "Partially adequate"
        INCORRECT = "INCORRECT", "Incorrect"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_version = models.ForeignKey(
        ContentVersion, on_delete=models.PROTECT, related_name="choices"
    )
    text = models.CharField(max_length=1000)
    position = models.PositiveSmallIntegerField()
    rating = models.CharField(max_length=9, choices=Rating.choices)
    consequence = models.TextField()
    explanation = models.TextField()

    class Meta:
        default_permissions = ("view",)
        ordering = ("content_version_id", "position", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("content_version", "position"),
                name="catalog_choice_version_position_unique",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1, position__lte=4),
                name="catalog_choice_position_bounded",
            ),
        ]


def validate_verification_checklist(value):
    if not isinstance(value, list) or not value:
        raise ValidationError("Verification checklist must be a non-empty list.")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValidationError(
            "Verification checklist entries must be non-empty strings."
        )


class LabExercise(ImmutableModel):
    """Optional append-only exercise for one content snapshot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_version = models.OneToOneField(
        ContentVersion,
        on_delete=models.PROTECT,
        related_name="lab_exercise",
    )
    objective = models.CharField(max_length=1000)
    initial_prompt = models.TextField()
    expected_artifact = models.TextField()
    verification_checklist = models.JSONField(
        validators=[validate_verification_checklist]
    )

    class Meta:
        default_permissions = ("view",)


class CatalogChangeLog(ImmutableModel):
    """Append-only outcome of an authenticated catalog command."""

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        EDIT = "EDIT", "Edit"
        ACTIVATE = "ACTIVATE", "Activate"
        DEACTIVATE = "DEACTIVATE", "Deactivate"
        REORDER = "REORDER", "Reorder"

    class EntityType(models.TextChoices):
        TRACK = "TRACK", "Track"
        MODULE = "MODULE", "Module"

    class Result(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        DENIED = "DENIED", "Denied"
        INVALID = "INVALID", "Invalid"
        CONFLICT = "CONFLICT", "Conflict"
        NOT_FOUND = "NOT_FOUND", "Not found"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="catalog_changes_performed",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    entity_type = models.CharField(max_length=6, choices=EntityType.choices)
    entity_id = models.UUIDField(null=True, blank=True)
    unresolved_reference_digest = models.CharField(max_length=64, null=True, blank=True)
    result = models.CharField(max_length=10, choices=Result.choices)
    changed = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=Q(entity_id__isnull=True)
                | Q(unresolved_reference_digest__isnull=True),
                name="catalog_change_reference_exclusive",
            ),
            models.CheckConstraint(
                condition=Q(result="SUCCESS") | Q(changed=False),
                name="catalog_change_failed_unchanged",
            ),
            models.CheckConstraint(
                condition=Q(changed=False)
                | Q(result="SUCCESS", entity_id__isnull=False),
                name="catalog_change_changed_success",
            ),
            models.CheckConstraint(
                condition=~Q(result="NOT_FOUND")
                | Q(unresolved_reference_digest__isnull=False),
                name="catalog_change_not_found_digest",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("actor", "occurred_at"), name="catalog_change_actor_idx"
            ),
            models.Index(
                fields=("entity_type", "entity_id", "occurred_at"),
                name="catalog_change_entity_idx",
            ),
            models.Index(
                fields=("entity_type", "unresolved_reference_digest", "occurred_at"),
                name="catalog_change_digest_idx",
            ),
            models.Index(
                fields=("result", "occurred_at"), name="catalog_change_result_idx"
            ),
        ]
