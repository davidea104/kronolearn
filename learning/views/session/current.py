"""Temporary entry point for the future daily-session workflow."""

from django.shortcuts import render

from accounts.security import active_account_required


@active_account_required
def current_session(request, track_id):
    return render(request, "learning/session/current.html")
