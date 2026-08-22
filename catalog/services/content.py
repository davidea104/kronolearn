"""Transactional catalog commands and append-only outcomes."""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from django.core.signing import salted_hmac
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import (
    CatalogChangeLog,
    CatalogState,
    ContentItem,
    ContentVersion,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
)


@dataclass(frozen=True)
class CatalogCommandOutcome:
    result: str
    changed: bool
    entity_type: str
    entity_id: object | None = None
    revision: int | None = None
    order_revision: int | None = None
    field_errors: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(
            self,
            "field_errors",
            MappingProxyType(dict(self.field_errors)),
        )


@dataclass(frozen=True)
class CatalogCommandTarget:
    actor: Account
    authorized: bool
    entity: object | None
    unresolved_reference: str | None


@dataclass(frozen=True)
class CatalogModuleTarget:
    actor: Account
    authorized: bool
    track: Track | None
    entity: Module | None
    modules: tuple[Module, ...]
    unresolved_reference: str | None


def publish_content_item(
    content_item: ContentItem,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentVersion:
    """Publish one immutable content snapshot in a future workflow.

    Preconditions: the item and actor are persisted, the payload describes a valid
    publishable snapshot, and the item's revision can be locked and validated.
    Result: a new immutable current ContentVersion; older snapshots stay unchanged.
    Ordering: version numbers increase under lock and item position is unchanged.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future atomic workflow rejects
    invalid payloads, stale revisions, and integrity conflicts without partial writes.
    Future authorization: reload and authorize the persisted actor as content_admin.
    Idempotency: no caller key exists; locked revision validation must prevent a
    duplicate publication for the same accepted revision.
    """
    raise NotImplementedError


def create_content_draft(
    module: Module,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentItem:
    """Create a content draft in a future locked authoring workflow.

    Preconditions: the module and actor are persisted and the payload is valid draft
    input for the module's current revision.
    Result: a draft ContentItem appended to the module's content sequence.
    Ordering: the future workflow allocates the next consecutive position under lock.
    Current effects: none; this STUB performs no reads, writes, events, or logging.
    Expected errors: currently NotImplementedError; the future atomic workflow rejects
    invalid payloads, stale revisions, and integrity conflicts without partial writes.
    Future authorization: reload and authorize the persisted actor as content_admin.
    Idempotency: no caller key exists; locked revision validation must prevent a
    duplicate draft for the same accepted request.
    """
    raise NotImplementedError


def get_published_version(content_item: ContentItem) -> ContentVersion | None:
    """Return the exact current published snapshot without version fallback."""
    if (
        content_item.status != ContentItem.Status.PUBLISHED
        or content_item.published_version < 1
    ):
        return None
    return ContentVersion.objects.filter(
        content_item=content_item,
        version_number=content_item.published_version,
    ).first()


def list_published_versions(track: Track) -> list[ContentVersion]:
    """List current snapshots for active modules in deterministic content order."""
    return list(
        ContentVersion.objects.filter(
            content_item__module__track=track,
            content_item__module__status=Module.Status.ACTIVE,
            content_item__status=ContentItem.Status.PUBLISHED,
            version_number=F("content_item__published_version"),
        )
        .select_related("content_item", "content_item__module")
        .order_by(
            "content_item__module__position",
            "content_item__position",
            "id",
        )
    )


def resolve_catalog_target(actor, model, requested_reference):
    """Lock the actor and resolve a target only after server-side authorization."""
    current_actor = Account.objects.select_for_update().get(pk=actor.pk)
    requested_reference = str(requested_reference)
    authorized = bool(
        current_actor.is_active
        and current_actor.groups.filter(name=CONTENT_ADMIN_ROLE).exists()
    )
    if not authorized:
        return CatalogCommandTarget(
            actor=current_actor,
            authorized=False,
            entity=None,
            unresolved_reference=requested_reference,
        )

    try:
        entity_id = uuid.UUID(requested_reference)
    except (AttributeError, TypeError, ValueError):
        entity_id = None
    entity = None
    if entity_id is not None:
        entity = model.objects.select_for_update().filter(pk=entity_id).first()
    return CatalogCommandTarget(
        actor=current_actor,
        authorized=True,
        entity=entity,
        unresolved_reference=(
            None
            if entity is not None
            else str(entity_id)
            if entity_id is not None
            else requested_reference
        ),
    )


def record_catalog_outcome(
    *,
    actor,
    action,
    entity_type,
    result,
    changed,
    entity_id=None,
    unresolved_reference=None,
    revision=None,
    order_revision=None,
    field_errors=None,
):
    digest = None
    if unresolved_reference is not None:
        digest = salted_hmac(
            f"catalog.{entity_type.casefold()}.reference",
            str(unresolved_reference),
            algorithm="sha256",
        ).hexdigest()
    CatalogChangeLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        unresolved_reference_digest=digest,
        result=result,
        changed=changed,
    )
    return CatalogCommandOutcome(
        result=result,
        changed=changed,
        entity_type=entity_type,
        entity_id=entity_id,
        revision=revision,
        order_revision=order_revision,
        field_errors=field_errors or {},
    )


def _locked_actor(actor):
    current_actor = Account.objects.select_for_update().get(pk=actor.pk)
    authorized = bool(
        current_actor.is_active
        and current_actor.groups.filter(name=CONTENT_ADMIN_ROLE).exists()
    )
    return current_actor, authorized


def _parse_uuid(reference):
    requested_reference = str(reference)
    try:
        return uuid.UUID(requested_reference), requested_reference
    except (AttributeError, TypeError, ValueError):
        return None, requested_reference


def resolve_module_target(actor, track_ref, module_ref=None):
    """Lock an authorized parent and its modules without exposing mismatches."""
    current_actor, authorized = _locked_actor(actor)
    track_id, requested_track = _parse_uuid(track_ref)
    requested_module = None if module_ref is None else str(module_ref)
    if not authorized:
        return CatalogModuleTarget(
            actor=current_actor,
            authorized=False,
            track=None,
            entity=None,
            modules=(),
            unresolved_reference=requested_module or requested_track,
        )
    track = None
    if track_id is not None:
        track = Track.objects.select_for_update().filter(pk=track_id).first()
    if track is None:
        return CatalogModuleTarget(
            actor=current_actor,
            authorized=True,
            track=None,
            entity=None,
            modules=(),
            unresolved_reference=str(track_id)
            if track_id is not None
            else requested_track,
        )
    modules = tuple(
        Module.objects.select_for_update().filter(track=track).order_by("pk")
    )
    if module_ref is None:
        return CatalogModuleTarget(
            actor=current_actor,
            authorized=True,
            track=track,
            entity=None,
            modules=modules,
            unresolved_reference=None,
        )
    module_id, requested_module = _parse_uuid(module_ref)
    entity = next((module for module in modules if module.pk == module_id), None)
    return CatalogModuleTarget(
        actor=current_actor,
        authorized=True,
        track=track,
        entity=entity,
        modules=modules,
        unresolved_reference=(
            None
            if entity is not None
            else str(module_id)
            if module_id is not None
            else requested_module
        ),
    )


def _validate_track_fields(*, title, description, audience):
    values = {
        "title": str(title).strip(),
        "description": str(description).strip(),
        "audience": str(audience).strip(),
    }
    limits = {"title": 160, "description": 2000, "audience": 500}
    errors = {}
    for field_name, value in values.items():
        if not value:
            errors[field_name] = ("Este campo es obligatorio.",)
        elif len(value) > limits[field_name]:
            errors[field_name] = (
                f"Asegúrate de que este valor tenga como máximo {limits[field_name]} caracteres.",
            )
    return values, errors


def _validate_publication(publication):
    publication = publication or {}
    source = str(publication.get("source", "")).strip()
    reviewed_on = publication.get("reviewed_on")
    editorial_status = publication.get("editorial_status")
    errors = {}
    if not source:
        errors["source"] = ("La fuente es obligatoria.",)
    elif len(source) > 500:
        errors["source"] = ("La fuente no puede superar 500 caracteres.",)
    if reviewed_on is None:
        errors["reviewed_on"] = ("La fecha de revisión es obligatoria.",)
    elif reviewed_on > timezone.localdate():
        errors["reviewed_on"] = ("La fecha de revisión no puede ser futura.",)
    if editorial_status != TrackVersion.EditorialStatus.APPROVED:
        errors["editorial_status"] = ("El contenido debe estar aprobado.",)
    return {
        "source": source,
        "reviewed_on": reviewed_on,
        "editorial_status": editorial_status,
    }, errors


def _publish_track(track, actor, publication):
    version_number = track.published_version + 1
    track.published_version = version_number
    TrackVersion.objects.create(
        track=track,
        version_number=version_number,
        title=track.title,
        description=track.description,
        audience=track.audience,
        author=actor,
        source=publication["source"],
        reviewed_on=publication["reviewed_on"],
        editorial_status=publication["editorial_status"],
    )


def _validate_module_fields(*, title, objective):
    values = {"title": str(title).strip(), "objective": str(objective).strip()}
    limits = {"title": 160, "objective": 1000}
    errors = {}
    for field_name, value in values.items():
        if not value:
            errors[field_name] = ("Este campo es obligatorio.",)
        elif len(value) > limits[field_name]:
            errors[field_name] = (
                f"Asegúrate de que este valor tenga como máximo {limits[field_name]} caracteres.",
            )
    return values, errors


def _publish_module(module, actor, publication):
    version_number = module.published_version + 1
    module.published_version = version_number
    ModuleVersion.objects.create(
        module=module,
        version_number=version_number,
        title=module.title,
        objective=module.objective,
        author=actor,
        source=publication["source"],
        reviewed_on=publication["reviewed_on"],
        editorial_status=publication["editorial_status"],
    )


@transaction.atomic
def create_track(actor, *, title, description, audience):
    current_actor, authorized = _locked_actor(actor)
    if not authorized:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
        )
    values, errors = _validate_track_fields(
        title=title,
        description=description,
        audience=audience,
    )
    if errors:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            field_errors=errors,
        )
    state = CatalogState.objects.select_for_update().get(pk=1)
    position = Track.objects.count() + 1
    try:
        with transaction.atomic():
            track = Track.objects.create(position=position, **values)
    except IntegrityError:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            field_errors={"title": ("Ya existe un track con este título.",)},
        )
    state.track_order_revision += 1
    state.save(update_fields=("track_order_revision",))
    return record_catalog_outcome(
        actor=current_actor,
        action=CatalogChangeLog.Action.CREATE,
        entity_type=CatalogChangeLog.EntityType.TRACK,
        entity_id=track.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=track.revision,
        order_revision=state.track_order_revision,
    )


@transaction.atomic
def edit_track(
    actor,
    track_ref,
    *,
    expected_revision,
    title,
    description,
    audience,
    publication=None,
):
    target = resolve_catalog_target(actor, Track, track_ref)
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.entity is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    track = target.entity
    if not isinstance(expected_revision, int) or expected_revision < 1:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=track.revision,
            field_errors={"expected_revision": ("La revisión no es válida.",)},
        )
    if track.revision != expected_revision:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            revision=track.revision,
        )
    values, errors = _validate_track_fields(
        title=title,
        description=description,
        audience=audience,
    )
    publication_values = None
    if track.status == Track.Status.ACTIVE:
        publication_values, publication_errors = _validate_publication(publication)
        errors.update(publication_errors)
    if errors:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=track.revision,
            field_errors=errors,
        )
    track.title = values["title"]
    track.description = values["description"]
    track.audience = values["audience"]
    track.revision += 1
    try:
        with transaction.atomic():
            if publication_values is not None:
                _publish_track(track, target.actor, publication_values)
            track.save()
    except IntegrityError:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=expected_revision,
            field_errors={"title": ("Ya existe un track con este título.",)},
        )
    return record_catalog_outcome(
        actor=target.actor,
        action=CatalogChangeLog.Action.EDIT,
        entity_type=CatalogChangeLog.EntityType.TRACK,
        entity_id=track.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=track.revision,
    )


@transaction.atomic
def change_track_status(
    actor,
    track_ref,
    *,
    expected_revision,
    target_status,
    publication=None,
):
    target = resolve_catalog_target(actor, Track, track_ref)
    action = (
        CatalogChangeLog.Action.ACTIVATE
        if target_status == Track.Status.ACTIVE
        else CatalogChangeLog.Action.DEACTIVATE
    )
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.entity is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    track = target.entity
    if not isinstance(expected_revision, int) or expected_revision < 1:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=track.revision,
            field_errors={"expected_revision": ("La revisión no es válida.",)},
        )
    if track.revision != expected_revision:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            revision=track.revision,
        )
    if target_status not in Track.Status.values:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=track.revision,
            field_errors={"status": ("Estado no soportado.",)},
        )
    if track.status == target_status:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=track.pk,
            result=CatalogChangeLog.Result.SUCCESS,
            changed=False,
            revision=track.revision,
        )
    publication_values = None
    if target_status == Track.Status.ACTIVE:
        publication_values, errors = _validate_publication(publication)
        modules = tuple(
            Module.objects.select_for_update().filter(track=track).order_by("pk")
        )
        if not any(module.status == Module.Status.ACTIVE for module in modules):
            errors["status"] = ("Activa al menos un módulo antes de publicar.",)
        if errors:
            return record_catalog_outcome(
                actor=target.actor,
                action=action,
                entity_type=CatalogChangeLog.EntityType.TRACK,
                entity_id=track.pk,
                result=CatalogChangeLog.Result.INVALID,
                changed=False,
                revision=track.revision,
                field_errors=errors,
            )
    track.status = target_status
    track.revision += 1
    if publication_values is not None:
        _publish_track(track, target.actor, publication_values)
    track.save()
    return record_catalog_outcome(
        actor=target.actor,
        action=action,
        entity_type=CatalogChangeLog.EntityType.TRACK,
        entity_id=track.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=track.revision,
    )


@transaction.atomic
def create_module(actor, track_ref, *, title, objective):
    target = resolve_module_target(actor, track_ref)
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.track is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    values, errors = _validate_module_fields(title=title, objective=objective)
    if errors:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            field_errors=errors,
        )
    try:
        with transaction.atomic():
            module = Module.objects.create(
                track=target.track,
                position=len(target.modules) + 1,
                **values,
            )
    except IntegrityError:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.CREATE,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            field_errors={"title": ("Ya existe un módulo con este título.",)},
        )
    target.track.module_order_revision += 1
    target.track.save(update_fields=("module_order_revision", "updated_at"))
    return record_catalog_outcome(
        actor=target.actor,
        action=CatalogChangeLog.Action.CREATE,
        entity_type=CatalogChangeLog.EntityType.MODULE,
        entity_id=module.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=module.revision,
        order_revision=target.track.module_order_revision,
    )


@transaction.atomic
def edit_module(
    actor,
    track_ref,
    module_ref,
    *,
    expected_revision,
    title,
    objective,
    publication=None,
):
    target = resolve_module_target(actor, track_ref, module_ref)
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.entity is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    module = target.entity
    if not isinstance(expected_revision, int) or expected_revision < 1:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=module.revision,
            field_errors={"expected_revision": ("La revisión no es válida.",)},
        )
    if module.revision != expected_revision:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            revision=module.revision,
        )
    values, errors = _validate_module_fields(title=title, objective=objective)
    publication_values = None
    if module.status == Module.Status.ACTIVE:
        publication_values, publication_errors = _validate_publication(publication)
        errors.update(publication_errors)
    if errors:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=module.revision,
            field_errors=errors,
        )
    module.title = values["title"]
    module.objective = values["objective"]
    module.revision += 1
    try:
        with transaction.atomic():
            if publication_values is not None:
                _publish_module(module, target.actor, publication_values)
            module.save()
    except IntegrityError:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.EDIT,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=expected_revision,
            field_errors={"title": ("Ya existe un módulo con este título.",)},
        )
    return record_catalog_outcome(
        actor=target.actor,
        action=CatalogChangeLog.Action.EDIT,
        entity_type=CatalogChangeLog.EntityType.MODULE,
        entity_id=module.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=module.revision,
    )


@transaction.atomic
def change_module_status(
    actor,
    track_ref,
    module_ref,
    *,
    expected_revision,
    target_status,
    publication=None,
):
    target = resolve_module_target(actor, track_ref, module_ref)
    action = (
        CatalogChangeLog.Action.ACTIVATE
        if target_status == Module.Status.ACTIVE
        else CatalogChangeLog.Action.DEACTIVATE
    )
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.entity is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    module = target.entity
    if not isinstance(expected_revision, int) or expected_revision < 1:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=module.revision,
            field_errors={"expected_revision": ("La revisión no es válida.",)},
        )
    if module.revision != expected_revision:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            revision=module.revision,
        )
    if target_status not in Module.Status.values:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            revision=module.revision,
            field_errors={"status": ("Estado no soportado.",)},
        )
    if module.status == target_status:
        return record_catalog_outcome(
            actor=target.actor,
            action=action,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=module.pk,
            result=CatalogChangeLog.Result.SUCCESS,
            changed=False,
            revision=module.revision,
        )
    publication_values = None
    if target_status == Module.Status.ACTIVE:
        publication_values, errors = _validate_publication(publication)
        if errors:
            return record_catalog_outcome(
                actor=target.actor,
                action=action,
                entity_type=CatalogChangeLog.EntityType.MODULE,
                entity_id=module.pk,
                result=CatalogChangeLog.Result.INVALID,
                changed=False,
                revision=module.revision,
                field_errors=errors,
            )
    elif target.track.status == Track.Status.ACTIVE:
        active_count = sum(
            item.status == Module.Status.ACTIVE for item in target.modules
        )
        if active_count == 1:
            return record_catalog_outcome(
                actor=target.actor,
                action=action,
                entity_type=CatalogChangeLog.EntityType.MODULE,
                entity_id=module.pk,
                result=CatalogChangeLog.Result.INVALID,
                changed=False,
                revision=module.revision,
                field_errors={
                    "status": ("Activa otro módulo o desactiva primero el track.",)
                },
            )
    module.status = target_status
    module.revision += 1
    if publication_values is not None:
        _publish_module(module, target.actor, publication_values)
    module.save()
    return record_catalog_outcome(
        actor=target.actor,
        action=action,
        entity_type=CatalogChangeLog.EntityType.MODULE,
        entity_id=module.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        revision=module.revision,
    )
