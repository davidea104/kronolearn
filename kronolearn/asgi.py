"""ASGI config for KronoLearn."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kronolearn.settings.production")

application = get_asgi_application()
