"""URL namespace for account workflows."""

from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.ThrottledLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("platform/roles/", views.role_management_view, name="role-management"),
    path(
        "platform/roles/<str:target_ref>/assign/",
        views.assign_content_role_view,
        name="assign-content-role",
    ),
    path(
        "platform/roles/<str:target_ref>/revoke/",
        views.revoke_content_role_view,
        name="revoke-content-role",
    ),
]
