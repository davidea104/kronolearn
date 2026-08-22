"""Namespaced composition for reserved learning routes."""

from django.urls import include, path

app_name = "learning"

urlpatterns = [
    path("learn/enrollments/", include("learning.urls.enrollment")),
    path("learn/session/", include("learning.urls.session")),
    path("learn/attempts/", include("learning.urls.attempts")),
    path("learn/progress/", include("learning.urls.progress")),
]
