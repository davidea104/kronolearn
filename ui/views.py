"""Learner-facing pages."""

from django.shortcuts import render

from accounts.security import active_account_required


@active_account_required
def learner_home(request):
    return render(request, "ui/learner_home.html")
