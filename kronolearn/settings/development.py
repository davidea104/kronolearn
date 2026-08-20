"""Development settings for KronoLearn."""

from .base import *
from .base import environment_bool

DEBUG = environment_bool("DEBUG", default=True)
if not DEBUG:
    raise RuntimeError("DEBUG must be True when using development settings.")

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
