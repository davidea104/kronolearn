"""Atomic catalog ordering commands."""

import uuid

from django.db import transaction
from django.db.models import F

from catalog.models import CatalogChangeLog, CatalogState, Module, Track
from catalog.services.content import (
    _locked_actor,
    record_catalog_outcome,
    resolve_module_target,
)


@transaction.atomic
def move_track(actor, track_ref, *, position, expected_order_revision):
    current_actor, authorized = _locked_actor(actor)
    requested_reference = str(track_ref)
    if not authorized:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=requested_reference,
        )
    try:
        track_id = uuid.UUID(requested_reference)
    except (AttributeError, TypeError, ValueError):
        track_id = None
    state = CatalogState.objects.select_for_update().get(pk=1)
    tracks_by_id = {
        track.pk: track for track in Track.objects.select_for_update().order_by("pk")
    }
    target = tracks_by_id.get(track_id)
    if target is None:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=str(track_id)
            if track_id is not None
            else requested_reference,
        )
    tracks = sorted(tracks_by_id.values(), key=lambda track: track.position)
    if not isinstance(expected_order_revision, int) or expected_order_revision < 0:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=target.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            order_revision=state.track_order_revision,
            field_errors={
                "expected_order_revision": ("La revisión de orden no es válida.",)
            },
        )
    if state.track_order_revision != expected_order_revision:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=target.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            order_revision=state.track_order_revision,
        )
    if not isinstance(position, int) or not 1 <= position <= len(tracks):
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=target.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            order_revision=state.track_order_revision,
            field_errors={"position": (f"Usa una posición entre 1 y {len(tracks)}.",)},
        )
    current_index = next(
        index for index, track in enumerate(tracks) if track.pk == target.pk
    )
    moved = tracks.pop(current_index)
    tracks.insert(position - 1, moved)
    changed_tracks = [
        track
        for new_position, track in enumerate(tracks, start=1)
        if track.position != new_position
    ]
    if not changed_tracks:
        return record_catalog_outcome(
            actor=current_actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.TRACK,
            entity_id=target.pk,
            result=CatalogChangeLog.Result.SUCCESS,
            changed=False,
            order_revision=state.track_order_revision,
        )
    offset = len(tracks) + 1
    Track.objects.update(position=F("position") + offset)
    for new_position, track in enumerate(tracks, start=1):
        if track in changed_tracks:
            track.revision += 1
        track.position = new_position
        track.save(update_fields=("position", "revision", "updated_at"))
    state.track_order_revision += 1
    state.save(update_fields=("track_order_revision",))
    return record_catalog_outcome(
        actor=current_actor,
        action=CatalogChangeLog.Action.REORDER,
        entity_type=CatalogChangeLog.EntityType.TRACK,
        entity_id=target.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        order_revision=state.track_order_revision,
    )


@transaction.atomic
def move_module(
    actor,
    track_ref,
    module_ref,
    *,
    position,
    expected_order_revision,
):
    target = resolve_module_target(actor, track_ref, module_ref)
    if not target.authorized:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.DENIED,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    if target.entity is None:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            result=CatalogChangeLog.Result.NOT_FOUND,
            changed=False,
            unresolved_reference=target.unresolved_reference,
        )
    track = target.track
    modules = sorted(target.modules, key=lambda module: module.position)
    if not isinstance(expected_order_revision, int) or expected_order_revision < 0:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=target.entity.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            order_revision=track.module_order_revision,
            field_errors={
                "expected_order_revision": ("La revisión de orden no es válida.",)
            },
        )
    if track.module_order_revision != expected_order_revision:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=target.entity.pk,
            result=CatalogChangeLog.Result.CONFLICT,
            changed=False,
            order_revision=track.module_order_revision,
        )
    if not isinstance(position, int) or not 1 <= position <= len(modules):
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=target.entity.pk,
            result=CatalogChangeLog.Result.INVALID,
            changed=False,
            order_revision=track.module_order_revision,
            field_errors={"position": (f"Usa una posición entre 1 y {len(modules)}.",)},
        )
    current_index = next(
        index for index, module in enumerate(modules) if module.pk == target.entity.pk
    )
    moved = modules.pop(current_index)
    modules.insert(position - 1, moved)
    changed_modules = [
        module
        for new_position, module in enumerate(modules, start=1)
        if module.position != new_position
    ]
    if not changed_modules:
        return record_catalog_outcome(
            actor=target.actor,
            action=CatalogChangeLog.Action.REORDER,
            entity_type=CatalogChangeLog.EntityType.MODULE,
            entity_id=target.entity.pk,
            result=CatalogChangeLog.Result.SUCCESS,
            changed=False,
            order_revision=track.module_order_revision,
        )
    offset = len(modules) + 1
    Module.objects.filter(track=track).update(position=F("position") + offset)
    for new_position, module in enumerate(modules, start=1):
        if module in changed_modules:
            module.revision += 1
        module.position = new_position
        module.save(update_fields=("position", "revision", "updated_at"))
    track.module_order_revision += 1
    track.save(update_fields=("module_order_revision", "updated_at"))
    return record_catalog_outcome(
        actor=target.actor,
        action=CatalogChangeLog.Action.REORDER,
        entity_type=CatalogChangeLog.EntityType.MODULE,
        entity_id=target.entity.pk,
        result=CatalogChangeLog.Result.SUCCESS,
        changed=True,
        order_revision=track.module_order_revision,
    )
