"""Root URL configuration for KronoLearn."""

from django.contrib import admin
from django.urls import path

from kronolearn.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
]
