"""Learner-facing pages."""

from django.conf import settings
from django.shortcuts import render

from accounts.security import active_account_required
from learning.services.enrollment import list_enrollments


@active_account_required
def learner_home(request):
    return render(
        request,
        "ui/learner_home.html",
        {"enrollments": list_enrollments(request.user)},
    )


def components_showroom(request):
    """Component showroom (DEBUG-only)."""
    if not settings.DEBUG:
        from django.http import Http404

        raise Http404("Component showroom is only available in DEBUG mode.")
    return render(request, "ui/components_showroom.html")
