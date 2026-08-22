"""Enrollment exploration and sign-up routes."""

from django.urls import path

from learning.views import enrollment as views

urlpatterns = [
    path("", views.enrollment_list, name="enrollment-list"),
    path("tracks/<str:track_id>/", views.enrollment_detail, name="enrollment-detail"),
    path(
        "tracks/<str:track_id>/enroll/",
        views.enrollment_enroll,
        name="enrollment-enroll",
    ),
]
