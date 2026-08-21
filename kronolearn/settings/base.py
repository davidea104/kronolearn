"""Shared Django settings for all KronoLearn environments."""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def required_environment(name: str) -> str:
    """Return a required environment variable without exposing its value."""
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"{name} must be set.")
    return value


def environment_bool(name: str, *, default: bool | None = None) -> bool:
    """Read an explicitly formatted boolean environment variable."""
    value = os.environ.get(name)
    if value is None:
        if default is None:
            raise ImproperlyConfigured(f"{name} must be set to True or False.")
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be set to True or False.")


def environment_nonnegative_int(name: str, *, default: int) -> int:
    value = os.environ.get(name, str(default))
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be a non-negative integer.") from exc
    if parsed < 0:
        raise ImproperlyConfigured(f"{name} must be a non-negative integer.")
    return parsed


def database_config(database_url: str) -> dict[str, object]:
    """Build Django's PostgreSQL database configuration from DATABASE_URL."""
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured(
            "DATABASE_URL must use the postgresql:// or postgres:// scheme."
        )
    if not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL must include a PostgreSQL host.")

    database_name = unquote(parsed.path.lstrip("/"))
    if not database_name:
        raise ImproperlyConfigured("DATABASE_URL must include a database name.")

    options = {
        key: values[-1]
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
    }
    config: dict[str, object] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": database_name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or ""),
    }
    if options:
        config["OPTIONS"] = options
    return config


SECRET_KEY = required_environment("SECRET_KEY")
DEBUG = environment_bool("DEBUG")
DATABASES = {"default": database_config(required_environment("DATABASE_URL"))}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "learning.apps.LearningConfig",
    "gamification.apps.GamificationConfig",
    "analytics.apps.AnalyticsConfig",
    "ui.apps.UiConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kronolearn.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "kronolearn.wsgi.application"
ASGI_APPLICATION = "kronolearn.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 15},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.Account"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "ui:learner-home"
LOGIN_TRUSTED_PROXY_COUNT = environment_nonnegative_int(
    "LOGIN_TRUSTED_PROXY_COUNT",
    default=0,
)
