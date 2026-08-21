"""Root URL configuration for KronoLearn."""

from django.contrib import admin
from django.urls import include, path

from kronolearn.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("ui.urls")),
    path("healthz", healthz, name="healthz"),
]
