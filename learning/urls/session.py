"""Reserved daily-session routes."""

from django.urls import path

from learning.views.session.current import current_session

urlpatterns = [
    path("<uuid:track_id>/", current_session, name="session-current"),
]
