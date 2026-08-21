"""URL namespace for catalog administration and learner views."""

from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("learn/catalog/", views.learner_track_list, name="track-list"),
    path(
        "learn/catalog/tracks/<str:track_id>/",
        views.learner_track_detail,
        name="track-detail",
    ),
    path(
        "learn/catalog/tracks/<str:track_id>/modules/<str:module_id>/",
        views.learner_module_detail,
        name="module-detail",
    ),
    path("catalog/manage/tracks/", views.manage_track_list, name="manage-track-list"),
    path(
        "catalog/manage/tracks/new/",
        views.manage_track_create,
        name="manage-track-create",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/edit/",
        views.manage_track_edit,
        name="manage-track-edit",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/activate/",
        views.manage_track_activate,
        name="manage-track-activate",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/deactivate/",
        views.manage_track_deactivate,
        name="manage-track-deactivate",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/position/",
        views.manage_track_reorder,
        name="manage-track-reorder",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/",
        views.manage_module_list,
        name="manage-module-list",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/new/",
        views.manage_module_create,
        name="manage-module-create",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/edit/",
        views.manage_module_edit,
        name="manage-module-edit",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/activate/",
        views.manage_module_activate,
        name="manage-module-activate",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/deactivate/",
        views.manage_module_deactivate,
        name="manage-module-deactivate",
    ),
    path(
        "catalog/manage/tracks/<str:track_ref>/modules/<str:module_ref>/position/",
        views.manage_module_reorder,
        name="manage-module-reorder",
    ),
]
