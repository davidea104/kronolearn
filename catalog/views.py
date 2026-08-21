"""HTTP adapters for catalog administration and learner exploration."""

from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.security import CONTENT_ADMIN_ROLE, active_account_required
from catalog.forms import (
    ModuleForm,
    ModulePositionForm,
    PublicationMetadataForm,
    TrackDeactivateForm,
    TrackForm,
    TrackPositionForm,
    TrackStateForm,
)
from catalog.models import CatalogChangeLog, Module, Track
from catalog.services.content import (
    change_module_status,
    change_track_status,
    create_module,
    create_track,
    edit_module,
    edit_track,
)
from catalog.services.ordering import move_module, move_track
from catalog.services.queries import (
    get_active_module,
    get_active_track,
    get_module_for_admin,
    get_track_for_admin,
    list_active_tracks,
    list_modules_for_admin,
    list_tracks_for_admin,
)

GENERIC_DENIAL = "No tienes permiso para realizar esta acción."
GENERIC_NOT_FOUND = "No se encontró el recurso solicitado."


class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303


def _has_content_role(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name=CONTENT_ADMIN_ROLE).exists()
    )


def _add_outcome_errors(form, outcome):
    for field_name, errors in outcome.field_errors.items():
        target = field_name if field_name in form.fields else None
        for error in errors:
            form.add_error(target, error)


def _track_list_context(actor):
    tracks, order_revision = list_tracks_for_admin(actor)
    return {"tracks": tracks, "track_order_revision": order_revision}


def _htmx_reorder_response(
    request,
    outcome,
    *,
    target,
    template,
    context,
    form,
):
    if not (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-Target") == target
        and outcome.result
        in {
            CatalogChangeLog.Result.SUCCESS,
            CatalogChangeLog.Result.INVALID,
            CatalogChangeLog.Result.CONFLICT,
        }
    ):
        return None
    _add_outcome_errors(form, outcome)
    if outcome.result == CatalogChangeLog.Result.CONFLICT:
        form.add_error(
            None,
            "El orden cambió en otra sesión. Recarga la página antes de reintentar.",
        )
    context["reorder_succeeded"] = outcome.result == CatalogChangeLog.Result.SUCCESS
    response = render(request, template, context)
    if outcome.result == CatalogChangeLog.Result.CONFLICT:
        response.status_code = 409
    return response


def _outcome_response(
    request,
    outcome,
    *,
    form=None,
    template=None,
    context=None,
    success_url=None,
):
    if outcome.result == CatalogChangeLog.Result.SUCCESS:
        if outcome.changed:
            messages.success(request, "El catálogo fue actualizado.")
        return HttpResponseSeeOther(success_url or reverse("catalog:manage-track-list"))
    if outcome.result == CatalogChangeLog.Result.DENIED:
        return HttpResponseForbidden(GENERIC_DENIAL)
    if outcome.result == CatalogChangeLog.Result.NOT_FOUND:
        return HttpResponseNotFound(GENERIC_NOT_FOUND)
    if form is not None:
        _add_outcome_errors(form, outcome)
    response = render(request, template, context or {"form": form})
    if outcome.result == CatalogChangeLog.Result.CONFLICT:
        response.status_code = 409
    return response


@active_account_required
@require_http_methods(["GET"])
def manage_track_list(request):
    if not _has_content_role(request.user):
        return HttpResponseForbidden(GENERIC_DENIAL)
    return render(
        request, "catalog/manage_track_list.html", _track_list_context(request.user)
    )


@active_account_required
@require_http_methods(["GET", "POST"])
def manage_track_create(request):
    if request.method == "GET":
        if not _has_content_role(request.user):
            return HttpResponseForbidden(GENERIC_DENIAL)
        return render(request, "catalog/manage_track_form.html", {"form": TrackForm()})
    form = TrackForm(request.POST)
    outcome = create_track(
        request.user,
        title=request.POST.get("title", ""),
        description=request.POST.get("description", ""),
        audience=request.POST.get("audience", ""),
    )
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_track_form.html",
        context={"form": form},
    )


@active_account_required
@require_http_methods(["GET", "POST"])
def manage_track_edit(request, track_ref):
    if request.method == "GET":
        if not _has_content_role(request.user):
            return HttpResponseForbidden(GENERIC_DENIAL)
        track = get_track_for_admin(request.user, track_ref)
        if track is None:
            return HttpResponseNotFound(GENERIC_NOT_FOUND)
        form = TrackForm(
            initial={
                "title": track.title,
                "description": track.description,
                "audience": track.audience,
                "expected_revision": track.revision,
            }
        )
        return render(
            request,
            "catalog/manage_track_form.html",
            {
                "form": form,
                "track": track,
                "publication_form": PublicationMetadataForm(),
            },
        )
    form = TrackForm(request.POST)
    publication_form = PublicationMetadataForm(request.POST)
    expected_revision = request.POST.get("expected_revision")
    try:
        expected_revision = int(expected_revision)
    except (TypeError, ValueError):
        expected_revision = -1
    publication = None
    if publication_form.is_valid():
        publication = publication_form.cleaned_data
    outcome = edit_track(
        request.user,
        track_ref,
        expected_revision=expected_revision,
        title=request.POST.get("title", ""),
        description=request.POST.get("description", ""),
        audience=request.POST.get("audience", ""),
        publication=publication,
    )
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_track_form.html",
        context={"form": form, "publication_form": publication_form},
    )


def _track_state_response(request, track_ref, target_status):
    form_class = (
        TrackStateForm if target_status == Track.Status.ACTIVE else TrackDeactivateForm
    )
    form = form_class(request.POST)
    expected_revision = request.POST.get("expected_revision")
    try:
        expected_revision = int(expected_revision)
    except (TypeError, ValueError):
        expected_revision = -1
    publication = (
        form.cleaned_data
        if form.is_valid() and target_status == Track.Status.ACTIVE
        else None
    )
    outcome = change_track_status(
        request.user,
        track_ref,
        expected_revision=expected_revision,
        target_status=target_status,
        publication=publication,
    )
    context = _track_list_context(request.user)
    context["state_form"] = form
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_track_list.html",
        context=context,
    )


@active_account_required
@require_POST
def manage_track_activate(request, track_ref):
    return _track_state_response(request, track_ref, Track.Status.ACTIVE)


@active_account_required
@require_POST
def manage_track_deactivate(request, track_ref):
    return _track_state_response(request, track_ref, Track.Status.INACTIVE)


@active_account_required
@require_POST
def manage_track_reorder(request, track_ref):
    form = TrackPositionForm(request.POST)
    form.is_valid()
    position = form.cleaned_data.get("position")
    expected_order_revision = form.cleaned_data.get("expected_order_revision")
    outcome = move_track(
        request.user,
        track_ref,
        position=position,
        expected_order_revision=expected_order_revision,
    )
    context = _track_list_context(request.user)
    context["position_form"] = form
    htmx_response = _htmx_reorder_response(
        request,
        outcome,
        target="track-rows",
        template="catalog/partials/track_rows.html",
        context=context,
        form=form,
    )
    if htmx_response is not None:
        return htmx_response
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_track_list.html",
        context=context,
    )


def _module_list_url(track_ref):
    return reverse(
        "catalog:manage-module-list",
        kwargs={"track_ref": str(track_ref)},
    )


def _module_list_context(actor, track_ref):
    track, modules, order_revision = list_modules_for_admin(actor, track_ref)
    return {
        "track": track,
        "modules": modules,
        "module_order_revision": order_revision,
    }


@active_account_required
@require_http_methods(["GET"])
def manage_module_list(request, track_ref):
    if not _has_content_role(request.user):
        return HttpResponseForbidden(GENERIC_DENIAL)
    context = _module_list_context(request.user, track_ref)
    if context["track"] is None:
        return HttpResponseNotFound(GENERIC_NOT_FOUND)
    return render(request, "catalog/manage_module_list.html", context)


@active_account_required
@require_http_methods(["GET", "POST"])
def manage_module_create(request, track_ref):
    if request.method == "GET":
        if not _has_content_role(request.user):
            return HttpResponseForbidden(GENERIC_DENIAL)
        track = get_track_for_admin(request.user, track_ref)
        if track is None:
            return HttpResponseNotFound(GENERIC_NOT_FOUND)
        return render(
            request,
            "catalog/manage_module_form.html",
            {"form": ModuleForm(), "track": track},
        )
    form = ModuleForm(request.POST)
    outcome = create_module(
        request.user,
        track_ref,
        title=request.POST.get("title", ""),
        objective=request.POST.get("objective", ""),
    )
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_module_form.html",
        context={"form": form},
        success_url=_module_list_url(track_ref),
    )


@active_account_required
@require_http_methods(["GET", "POST"])
def manage_module_edit(request, track_ref, module_ref):
    if request.method == "GET":
        if not _has_content_role(request.user):
            return HttpResponseForbidden(GENERIC_DENIAL)
        track, module = get_module_for_admin(request.user, track_ref, module_ref)
        if module is None:
            return HttpResponseNotFound(GENERIC_NOT_FOUND)
        form = ModuleForm(
            initial={
                "title": module.title,
                "objective": module.objective,
                "expected_revision": module.revision,
            }
        )
        return render(
            request,
            "catalog/manage_module_form.html",
            {
                "form": form,
                "track": track,
                "module": module,
                "publication_form": PublicationMetadataForm(),
            },
        )
    form = ModuleForm(request.POST)
    publication_form = PublicationMetadataForm(request.POST)
    try:
        expected_revision = int(request.POST.get("expected_revision"))
    except (TypeError, ValueError):
        expected_revision = -1
    publication = publication_form.cleaned_data if publication_form.is_valid() else None
    outcome = edit_module(
        request.user,
        track_ref,
        module_ref,
        expected_revision=expected_revision,
        title=request.POST.get("title", ""),
        objective=request.POST.get("objective", ""),
        publication=publication,
    )
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_module_form.html",
        context={"form": form, "publication_form": publication_form},
        success_url=_module_list_url(track_ref),
    )


def _module_state_response(request, track_ref, module_ref, target_status):
    form_class = (
        TrackStateForm if target_status == Module.Status.ACTIVE else TrackDeactivateForm
    )
    form = form_class(request.POST)
    try:
        expected_revision = int(request.POST.get("expected_revision"))
    except (TypeError, ValueError):
        expected_revision = -1
    publication = (
        form.cleaned_data
        if form.is_valid() and target_status == Module.Status.ACTIVE
        else None
    )
    outcome = change_module_status(
        request.user,
        track_ref,
        module_ref,
        expected_revision=expected_revision,
        target_status=target_status,
        publication=publication,
    )
    context = _module_list_context(request.user, track_ref)
    context["state_form"] = form
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_module_list.html",
        context=context,
        success_url=_module_list_url(track_ref),
    )


@active_account_required
@require_POST
def manage_module_activate(request, track_ref, module_ref):
    return _module_state_response(request, track_ref, module_ref, Module.Status.ACTIVE)


@active_account_required
@require_POST
def manage_module_deactivate(request, track_ref, module_ref):
    return _module_state_response(
        request, track_ref, module_ref, Module.Status.INACTIVE
    )


@active_account_required
@require_POST
def manage_module_reorder(request, track_ref, module_ref):
    form = ModulePositionForm(request.POST)
    form.is_valid()
    position = form.cleaned_data.get("position")
    expected_order_revision = form.cleaned_data.get("expected_order_revision")
    outcome = move_module(
        request.user,
        track_ref,
        module_ref,
        position=position,
        expected_order_revision=expected_order_revision,
    )
    context = _module_list_context(request.user, track_ref)
    context["position_form"] = form
    htmx_response = _htmx_reorder_response(
        request,
        outcome,
        target="module-rows",
        template="catalog/partials/module_rows.html",
        context=context,
        form=form,
    )
    if htmx_response is not None:
        return htmx_response
    return _outcome_response(
        request,
        outcome,
        form=form,
        template="catalog/manage_module_list.html",
        context=context,
        success_url=_module_list_url(track_ref),
    )


@active_account_required
@require_http_methods(["GET"])
def learner_track_list(request):
    return render(
        request,
        "catalog/learner_track_list.html",
        {"tracks": list_active_tracks()},
    )


@active_account_required
@require_http_methods(["GET"])
def learner_track_detail(request, track_id):
    track = get_active_track(track_id)
    if track is None:
        return HttpResponseNotFound(GENERIC_NOT_FOUND)
    return render(
        request,
        "catalog/learner_track_detail.html",
        {"track": track, "modules": track.active_modules},
    )


@active_account_required
@require_http_methods(["GET"])
def learner_module_detail(request, track_id, module_id):
    module = get_active_module(track_id, module_id)
    if module is None:
        return HttpResponseNotFound(GENERIC_NOT_FOUND)
    return render(
        request,
        "catalog/learner_track_detail.html",
        {"module": module},
    )
