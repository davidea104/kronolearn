"""Authorized catalog read models."""

import uuid

from django.db.models import Prefetch

from accounts.security import CONTENT_ADMIN_ROLE
from catalog.models import CatalogState, Module, Track


def _can_manage_catalog(actor):
    return bool(
        actor.is_authenticated
        and actor.is_active
        and actor.groups.filter(name=CONTENT_ADMIN_ROLE).exists()
    )


def list_tracks_for_admin(actor):
    if not _can_manage_catalog(actor):
        return Track.objects.none(), None
    state = CatalogState.objects.get(pk=1)
    return Track.objects.order_by("position", "id"), state.track_order_revision


def get_track_for_admin(actor, track_ref):
    if not _can_manage_catalog(actor):
        return None
    try:
        track_id = uuid.UUID(str(track_ref))
    except (AttributeError, TypeError, ValueError):
        return None
    return Track.objects.filter(pk=track_id).first()


def list_modules_for_admin(actor, track_ref):
    track = get_track_for_admin(actor, track_ref)
    if track is None:
        return None, Module.objects.none(), None
    modules = Module.objects.filter(track=track).order_by("position", "id")
    return track, modules, track.module_order_revision


def get_module_for_admin(actor, track_ref, module_ref):
    track = get_track_for_admin(actor, track_ref)
    if track is None:
        return None, None
    try:
        module_id = uuid.UUID(str(module_ref))
    except (AttributeError, TypeError, ValueError):
        return track, None
    module = Module.objects.filter(track=track, pk=module_id).first()
    return track, module


TRACK_LEARNER_FIELDS = ("id", "title", "description", "audience", "position")
MODULE_LEARNER_FIELDS = ("id", "track_id", "title", "objective", "position")


def _uuid_or_none(value):
    try:
        return uuid.UUID(str(value))
    except (AttributeError, TypeError, ValueError):
        return None


def list_active_tracks():
    return (
        Track.objects.filter(status=Track.Status.ACTIVE)
        .only(*TRACK_LEARNER_FIELDS)
        .order_by("position", "id")
    )


def get_active_track(track_id):
    track_id = _uuid_or_none(track_id)
    if track_id is None:
        return None
    active_modules = (
        Module.objects.filter(status=Module.Status.ACTIVE)
        .only(*MODULE_LEARNER_FIELDS)
        .order_by("position", "id")
    )
    return (
        Track.objects.filter(pk=track_id, status=Track.Status.ACTIVE)
        .only(*TRACK_LEARNER_FIELDS)
        .prefetch_related(
            Prefetch("modules", queryset=active_modules, to_attr="active_modules")
        )
        .first()
    )


def get_active_module(track_id, module_id):
    track_id = _uuid_or_none(track_id)
    module_id = _uuid_or_none(module_id)
    if track_id is None or module_id is None:
        return None
    return (
        Module.objects.filter(
            pk=module_id,
            track_id=track_id,
            status=Module.Status.ACTIVE,
            track__status=Track.Status.ACTIVE,
        )
        .only(*MODULE_LEARNER_FIELDS)
        .first()
    )
