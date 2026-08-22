"""HTTP adapters for enrollment exploration."""

from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from accounts.security import active_account_required
from catalog.services.queries import get_active_track, list_active_tracks
from learning.services.enrollment import get_enrollment

# Duplicated text, not the catalog.views constant: see contracts/enrollment.md.
GENERIC_NOT_FOUND = "No se encontró el recurso solicitado."


def _track_card_context(account, track):
    return {
        "track": track,
        "module_count": len(track.active_modules),
        "is_enrolled": get_enrollment(account, track) is not None,
    }


@active_account_required
@require_http_methods(["GET"])
def enrollment_list(request):
    cards = [
        _track_card_context(request.user, get_active_track(track.id))
        for track in list_active_tracks()
    ]
    return render(request, "learning/enrollment/list.html", {"cards": cards})


@active_account_required
@require_http_methods(["GET"])
def enrollment_detail(request, track_id):
    track = get_active_track(track_id)
    if track is None:
        return HttpResponseNotFound(GENERIC_NOT_FOUND)
    return render(
        request,
        "learning/enrollment/detail.html",
        _track_card_context(request.user, track),
    )
