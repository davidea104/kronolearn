"""Transactional catalog commands and append-only outcomes."""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

from django.core.exceptions import ValidationError
from django.core.signing import salted_hmac
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE
from accounts.services.queries import resolve_content_admin
from catalog.content_data.definitions import (
    PRIMARY_TRACK_TITLE,
    SECONDARY_TRACK_TITLE,
)
from catalog.models import (
    CatalogChangeLog,
    CatalogState,
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    ModuleVersion,
    Track,
    TrackVersion,
    canonicalize_title,
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


class ContentRevisionConflict(Exception):
    """Raised when a content write loses optimistic concurrency."""


class ContentLoadConflict(Exception):
    """Raised when existing catalog data cannot be safely reconciled."""


@dataclass(frozen=True)
class ContentLoadOutcome:
    changed: bool
    track_count: int
    module_count: int
    content_item_count: int
    items_created: int
    versions_created: int


def _validate_load_definitions(definitions) -> None:
    expected = ((PRIMARY_TRACK_TITLE, 7, True), (SECONDARY_TRACK_TITLE, 3, False))
    if type(definitions) is not tuple or len(definitions) != 2:
        raise ValidationError("La definición de contenido no es válida.")
    for definition, (title, unit_count, has_labs) in zip(
        definitions, expected, strict=True
    ):
        units = definition.module.units
        if (
            definition.title != title
            or len(units) != unit_count
            or tuple(unit.position for unit in units) != tuple(range(1, unit_count + 1))
            or any((unit.lab is not None) != has_labs for unit in units)
        ):
            raise ValidationError("La definición de contenido no es válida.")


def _publication(source, reviewed_on, editorial_status):
    return {
        "source": source,
        "reviewed_on": reviewed_on,
        "editorial_status": editorial_status,
    }


def _require_catalog_success(outcome) -> None:
    if outcome.result != CatalogChangeLog.Result.SUCCESS:
        raise ContentLoadConflict("Learning content could not be reconciled.")


def _content_payload(unit, expected_revision):
    return {
        "expected_revision": expected_revision,
        "title": unit.title,
        "learning_objective": unit.learning_objective,
        "lesson_text": unit.lesson_text,
        "case_prompt": unit.case_prompt,
        "source": unit.source,
        "reviewed_on": unit.reviewed_on,
        "choices": tuple(
            {
                "position": choice.position,
                "text": choice.text,
                "rating": choice.rating,
                "consequence": choice.consequence,
                "explanation": choice.explanation,
            }
            for choice in unit.choices
        ),
        "lab": (
            None
            if unit.lab is None
            else {
                "objective": unit.lab.objective,
                "initial_prompt": unit.lab.initial_prompt,
                "expected_artifact": unit.lab.expected_artifact,
                "verification_checklist": unit.lab.verification_checklist,
            }
        ),
    }


def _choice_snapshot(version):
    return tuple(
        version.choices.order_by("position").values_list(
            "position",
            "text",
            "rating",
            "consequence",
            "explanation",
        )
    )


def _defined_choices(choices):
    return tuple(
        (
            choice.position,
            choice.text,
            choice.rating,
            choice.consequence,
            choice.explanation,
        )
        for choice in choices
    )


def _lab_snapshot(version):
    try:
        lab = version.lab_exercise
    except LabExercise.DoesNotExist:
        return None
    return (
        lab.objective,
        lab.initial_prompt,
        lab.expected_artifact,
        tuple(lab.verification_checklist),
    )


def _defined_lab(lab):
    if lab is None:
        return None
    return (
        lab.objective,
        lab.initial_prompt,
        lab.expected_artifact,
        tuple(lab.verification_checklist),
    )


def _matches_unit(version, unit) -> bool:
    return (
        version.title == unit.title
        and version.learning_objective == unit.learning_objective
        and version.lesson_text == unit.lesson_text
        and version.case_prompt == unit.case_prompt
        and version.source == unit.source
        and version.reviewed_on == unit.reviewed_on
        and version.editorial_status == ContentVersion.EditorialStatus.PUBLISHED
        and _choice_snapshot(version) == _defined_choices(unit.choices)
        and _lab_snapshot(version) == _defined_lab(unit.lab)
    )


def _matches_legacy(version, fingerprint) -> bool:
    return fingerprint is not None and (
        version.title == fingerprint.title
        and version.learning_objective == fingerprint.learning_objective
        and version.lesson_text == fingerprint.lesson_text
        and version.case_prompt == fingerprint.case_prompt
        and version.source == fingerprint.source
        and _choice_snapshot(version) == _defined_choices(fingerprint.choices)
        and _lab_snapshot(version) == _defined_lab(fingerprint.lab)
    )


def _current_content_version(item):
    if item.status != ContentItem.Status.PUBLISHED or item.published_version < 1:
        return None
    return (
        ContentVersion.objects.select_for_update()
        .filter(
            content_item=item,
            version_number=item.published_version,
        )
        .first()
    )


def _content_item_is_managed(item, unit) -> bool:
    if item.status == ContentItem.Status.DRAFT and not item.versions.exists():
        return True
    version = _current_content_version(item)
    if version is None:
        return False
    return version.source.startswith(unit.source_marker) or _matches_legacy(
        version, unit.legacy_fingerprint
    )


def _resolve_track(actor, definition):
    title_keys = {
        canonicalize_title(definition.title),
        *(canonicalize_title(title) for title in definition.legacy_titles),
    }
    matches = list(Track.objects.select_for_update().filter(title_key__in=title_keys))
    if len(matches) > 1:
        raise ContentLoadConflict("Learning content could not be reconciled.")
    changed = False
    if matches:
        track = matches[0]
    else:
        outcome = create_track(
            actor,
            title=definition.title,
            description=definition.description,
            audience=definition.audience,
        )
        _require_catalog_success(outcome)
        track = Track.objects.select_for_update().get(pk=outcome.entity_id)
        changed = True

    if (
        track.title != definition.title
        or track.description != definition.description
        or track.audience != definition.audience
    ):
        outcome = edit_track(
            actor,
            str(track.pk),
            expected_revision=track.revision,
            title=definition.title,
            description=definition.description,
            audience=definition.audience,
            publication=(
                _publication(
                    definition.source,
                    definition.reviewed_on,
                    TrackVersion.EditorialStatus.APPROVED,
                )
                if track.status == Track.Status.ACTIVE
                else None
            ),
        )
        _require_catalog_success(outcome)
        track.refresh_from_db()
        changed = True
    return track, changed


def _resolve_module(actor, track, definition):
    module = (
        Module.objects.select_for_update()
        .filter(
            track=track,
            title_key=canonicalize_title(definition.title),
        )
        .first()
    )
    changed = False
    if module is None:
        outcome = create_module(
            actor,
            str(track.pk),
            title=definition.title,
            objective=definition.objective,
        )
        _require_catalog_success(outcome)
        module = Module.objects.select_for_update().get(pk=outcome.entity_id)
        track.refresh_from_db()
        changed = True
    elif module.objective != definition.objective:
        outcome = edit_module(
            actor,
            str(track.pk),
            str(module.pk),
            expected_revision=module.revision,
            title=definition.title,
            objective=definition.objective,
            publication=(
                _publication(
                    definition.source,
                    definition.reviewed_on,
                    ModuleVersion.EditorialStatus.APPROVED,
                )
                if module.status == Module.Status.ACTIVE
                else None
            ),
        )
        _require_catalog_success(outcome)
        module.refresh_from_db()
        changed = True
    return module, changed


def _validate_existing_content(module, units):
    items = tuple(
        ContentItem.objects.select_for_update()
        .filter(module=module)
        .order_by("position")
    )
    positions = tuple(item.position for item in items)
    if len(items) > len(units) or positions != tuple(range(1, len(items) + 1)):
        raise ContentLoadConflict("Learning content could not be reconciled.")
    if any(
        not _content_item_is_managed(item, units[item.position - 1]) for item in items
    ):
        raise ContentLoadConflict("Learning content could not be reconciled.")
    return {item.position: item for item in items}


def _activate_module(actor, track, module, definition) -> bool:
    module.refresh_from_db()
    if module.status == Module.Status.ACTIVE:
        return False
    outcome = change_module_status(
        actor,
        str(track.pk),
        str(module.pk),
        expected_revision=module.revision,
        target_status=Module.Status.ACTIVE,
        publication=_publication(
            definition.source,
            definition.reviewed_on,
            ModuleVersion.EditorialStatus.APPROVED,
        ),
    )
    _require_catalog_success(outcome)
    return True


def _activate_track(actor, track, definition) -> bool:
    track.refresh_from_db()
    if track.status == Track.Status.ACTIVE:
        return False
    outcome = change_track_status(
        actor,
        str(track.pk),
        expected_revision=track.revision,
        target_status=Track.Status.ACTIVE,
        publication=_publication(
            definition.source,
            definition.reviewed_on,
            TrackVersion.EditorialStatus.APPROVED,
        ),
    )
    _require_catalog_success(outcome)
    return True


@transaction.atomic
def load_learning_content(actor_ref, definitions) -> ContentLoadOutcome:
    """Atomically reconcile the approved learning corpus."""
    _validate_load_definitions(definitions)
    actor = resolve_content_admin(actor_ref, for_update=True)
    CatalogState.objects.select_for_update().get(pk=1)
    changed = False
    items_created = 0
    versions_created = 0

    for definition in definitions:
        track, track_changed = _resolve_track(actor, definition)
        module, module_changed = _resolve_module(actor, track, definition.module)
        changed = changed or track_changed or module_changed
        existing_items = _validate_existing_content(module, definition.module.units)

        for unit in definition.module.units:
            item = existing_items.get(unit.position)
            if item is None:
                item = create_content_draft(
                    module,
                    actor,
                    {"expected_revision": module.revision},
                )
                module.refresh_from_db()
                items_created += 1
                changed = True
            version = _current_content_version(item)
            if version is None or not _matches_unit(version, unit):
                publish_content_item(
                    item,
                    actor,
                    _content_payload(unit, item.revision),
                )
                versions_created += 1
                changed = True

        changed = _activate_module(actor, track, module, definition.module) or changed
        changed = _activate_track(actor, track, definition) or changed

    return ContentLoadOutcome(
        changed=changed,
        track_count=2,
        module_count=2,
        content_item_count=10,
        items_created=items_created,
        versions_created=versions_created,
    )


def _expected_revision(payload: Mapping[str, object]) -> int:
    if not isinstance(payload, Mapping):
        raise ValidationError("El contenido no es válido.")
    expected_revision = payload.get("expected_revision")
    if type(expected_revision) is not int or expected_revision < 1:
        raise ValidationError({"expected_revision": ("La revisión no es válida.",)})
    return expected_revision


def _required_text(value, field_name, *, max_length=None):
    if type(value) is not str or not value.strip():
        raise ValidationError({field_name: ("Este campo es obligatorio.",)})
    normalized = value.strip()
    if max_length is not None and len(normalized) > max_length:
        raise ValidationError(
            {field_name: (f"Este campo no puede superar {max_length} caracteres.",)}
        )
    return normalized


def _validate_choices(value):
    if type(value) not in (list, tuple) or len(value) not in (3, 4):
        raise ValidationError({"choices": ("Debe haber tres o cuatro opciones.",)})
    choices = []
    allowed_keys = {"position", "text", "rating", "consequence", "explanation"}
    for raw_choice in value:
        if not isinstance(raw_choice, Mapping) or set(raw_choice) != allowed_keys:
            raise ValidationError({"choices": ("Una opción no es válida.",)})
        position = raw_choice["position"]
        if type(position) is not int or position < 1:
            raise ValidationError({"choices": ("Las posiciones no son válidas.",)})
        rating = raw_choice["rating"]
        if rating not in Choice.Rating.values:
            raise ValidationError({"choices": ("La valoración no es válida.",)})
        choices.append(
            {
                "position": position,
                "text": _required_text(raw_choice["text"], "choices", max_length=1000),
                "rating": rating,
                "consequence": _required_text(raw_choice["consequence"], "choices"),
                "explanation": _required_text(raw_choice["explanation"], "choices"),
            }
        )
    if [choice["position"] for choice in choices] != list(range(1, len(choices) + 1)):
        raise ValidationError({"choices": ("Las posiciones no son consecutivas.",)})
    if len({choice["text"].casefold() for choice in choices}) != len(choices):
        raise ValidationError({"choices": ("Las opciones deben ser distintas.",)})
    if not any(choice["rating"] == Choice.Rating.OPTIMAL for choice in choices):
        raise ValidationError({"choices": ("Se requiere una opción óptima.",)})
    return tuple(choices)


def _validate_lab(value):
    if value is None:
        return None
    allowed_keys = {
        "objective",
        "initial_prompt",
        "expected_artifact",
        "verification_checklist",
    }
    if not isinstance(value, Mapping) or set(value) != allowed_keys:
        raise ValidationError({"lab": ("El laboratorio no es válido.",)})
    checklist = value["verification_checklist"]
    if type(checklist) not in (list, tuple) or not checklist:
        raise ValidationError({"lab": ("La lista de verificación es obligatoria.",)})
    return {
        "objective": _required_text(value["objective"], "lab", max_length=1000),
        "initial_prompt": _required_text(value["initial_prompt"], "lab"),
        "expected_artifact": _required_text(value["expected_artifact"], "lab"),
        "verification_checklist": tuple(
            _required_text(entry, "lab") for entry in checklist
        ),
    }


def _validate_content_publication(payload):
    allowed_keys = {
        "expected_revision",
        "title",
        "learning_objective",
        "lesson_text",
        "case_prompt",
        "source",
        "reviewed_on",
        "choices",
        "lab",
    }
    if not isinstance(payload, Mapping) or set(payload) != allowed_keys:
        raise ValidationError("El contenido no es válido.")
    reviewed_on = payload["reviewed_on"]
    if type(reviewed_on) is not date:
        raise ValidationError(
            {"reviewed_on": ("La fecha de revisión es obligatoria.",)}
        )
    if reviewed_on > timezone.localdate():
        raise ValidationError(
            {"reviewed_on": ("La fecha de revisión no puede ser futura.",)}
        )
    return {
        "title": _required_text(payload["title"], "title", max_length=160),
        "learning_objective": _required_text(
            payload["learning_objective"],
            "learning_objective",
            max_length=1000,
        ),
        "lesson_text": _required_text(payload["lesson_text"], "lesson_text"),
        "case_prompt": _required_text(payload["case_prompt"], "case_prompt"),
        "source": _required_text(payload["source"], "source", max_length=500),
        "reviewed_on": reviewed_on,
        "choices": _validate_choices(payload["choices"]),
        "lab": _validate_lab(payload["lab"]),
    }


@transaction.atomic
def publish_content_item(
    content_item: ContentItem,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentVersion:
    """Publish one complete immutable content snapshot atomically.

    Preconditions: persisted item and authorized actor with a valid revision payload.
    Result: a new current immutable version with choices and optional laboratory.
    Ordering: version numbers increase while the content position stays unchanged.
    Current effects: creates a snapshot and advances item publication state atomically.
    Expected errors: validation, authorization, or content revision conflict.
    Future authorization: no deferred authorization; the account service owns it now.
    Idempotency: the locked expected revision prevents duplicate accepted publication.
    """
    expected_revision = _expected_revision(payload)
    current_actor = resolve_content_admin(
        str(getattr(actor, "pk", "")), for_update=True
    )
    locked_item = (
        ContentItem.objects.select_for_update()
        .filter(pk=getattr(content_item, "pk", None))
        .first()
    )
    if locked_item is None:
        raise ValidationError({"content_item": ("La unidad no es válida.",)})
    if locked_item.revision != expected_revision:
        raise ContentRevisionConflict("Content revision conflict.")
    values = _validate_content_publication(payload)

    version_number = locked_item.published_version + 1
    try:
        with transaction.atomic():
            version = ContentVersion.objects.create(
                content_item=locked_item,
                version_number=version_number,
                title=values["title"],
                learning_objective=values["learning_objective"],
                lesson_text=values["lesson_text"],
                case_prompt=values["case_prompt"],
                source=values["source"],
                author=current_actor,
                reviewed_on=values["reviewed_on"],
                editorial_status=ContentVersion.EditorialStatus.PUBLISHED,
            )
            for choice in values["choices"]:
                Choice.objects.create(
                    content_version=version,
                    position=choice["position"],
                    text=choice["text"],
                    rating=choice["rating"],
                    consequence=choice["consequence"],
                    explanation=choice["explanation"],
                )
            lab = values["lab"]
            if lab is not None:
                LabExercise.objects.create(
                    content_version=version,
                    objective=lab["objective"],
                    initial_prompt=lab["initial_prompt"],
                    expected_artifact=lab["expected_artifact"],
                    verification_checklist=list(lab["verification_checklist"]),
                )
            locked_item.status = ContentItem.Status.PUBLISHED
            locked_item.published_version = version_number
            locked_item.revision += 1
            locked_item.save(
                update_fields=(
                    "status",
                    "published_version",
                    "revision",
                    "updated_at",
                )
            )
    except IntegrityError as exc:
        raise ContentRevisionConflict("Content revision conflict.") from exc
    return version


@transaction.atomic
def create_content_draft(
    module: Module,
    actor: Account,
    payload: Mapping[str, object],
) -> ContentItem:
    """Append a draft after locking its authorized actor and parent module.

    Preconditions: persisted module and authorized actor with its expected revision.
    Result: a draft content item at the next consecutive position.
    Ordering: allocation occurs under the module lock and increments its revision.
    Current effects: creates one draft and advances the parent revision atomically.
    Expected errors: validation, authorization, or content revision conflict.
    Future authorization: no deferred authorization; the account service owns it now.
    Idempotency: the locked expected revision prevents duplicate accepted creation.
    """
    expected_revision = _expected_revision(payload)
    resolve_content_admin(str(getattr(actor, "pk", "")), for_update=True)
    locked_module = (
        Module.objects.select_for_update()
        .filter(pk=getattr(module, "pk", None))
        .first()
    )
    if locked_module is None:
        raise ValidationError({"module": ("El módulo no es válido.",)})
    if locked_module.revision != expected_revision:
        raise ContentRevisionConflict("Content revision conflict.")

    positions = list(
        ContentItem.objects.select_for_update()
        .filter(module=locked_module)
        .order_by("position")
        .values_list("position", flat=True)
    )
    if positions != list(range(1, len(positions) + 1)):
        raise ValidationError(
            {"position": ("La secuencia de contenido no es válida.",)}
        )

    try:
        with transaction.atomic():
            item = ContentItem.objects.create(
                module=locked_module,
                position=len(positions) + 1,
            )
            locked_module.revision += 1
            locked_module.save(update_fields=("revision", "updated_at"))
    except IntegrityError as exc:
        raise ContentRevisionConflict("Content revision conflict.") from exc
    return item


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
