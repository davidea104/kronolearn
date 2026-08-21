"""URL namespace for learner-facing pages."""

from django.urls import path

from ui import views

app_name = "ui"

urlpatterns = [
    path("learn/", views.learner_home, name="learner-home"),
]
