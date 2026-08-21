"""Security primitives shared by account workflows."""

import hashlib
import hmac
import ipaddress
from functools import wraps
from types import MappingProxyType
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import logout
from django.urls import Resolver404, resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme

LEARNER_ROLE = "learner"
CONTENT_ADMIN_ROLE = "content_admin"


def canonicalize_account_email(raw_email: str) -> str:
    """Return the single persisted and compared representation of an email."""
    return raw_email.strip().casefold()


def security_digest(value: str, *, purpose: str) -> str:
    """Create a deterministic purpose-separated reference without storing input."""
    key = hashlib.sha256(f"{settings.SECRET_KEY}:{purpose}".encode()).digest()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def request_origin(request) -> str:
    """Return a canonical client IP using only the configured trusted proxy chain."""
    remote_address = request.META.get("REMOTE_ADDR", "")
    candidate = remote_address
    trusted_proxy_count = settings.LOGIN_TRUSTED_PROXY_COUNT
    if trusted_proxy_count:
        forwarded_for = [
            value.strip()
            for value in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
            if value.strip()
        ]
        if len(forwarded_for) >= trusted_proxy_count:
            candidate = forwarded_for[-trusted_proxy_count]
    try:
        return ipaddress.ip_address(candidate).compressed
    except ValueError:
        return "unknown"


def _active_account(user) -> bool:
    return bool(user.is_authenticated and user.is_active)


def _platform_admin(user) -> bool:
    return bool(_active_account(user) and user.is_superuser)


def active_account_required(view_func):
    @wraps(view_func)
    def guarded_view(request, *args, **kwargs):
        if not _active_account(request.user):
            from django.contrib.auth.views import redirect_to_login

            logout(request)
            return redirect_to_login(
                request.get_full_path(),
                login_url=reverse("accounts:login"),
            )
        return view_func(request, *args, **kwargs)

    return guarded_view


SAFE_RETURN_ROUTES = MappingProxyType(
    {
        "ui:learner-home": _active_account,
        "accounts:profile": _active_account,
        "accounts:role-management": _platform_admin,
    }
)


def resolve_safe_next(candidate: str, *, request, user) -> str:
    """Return an authorized same-origin GET destination or learner home."""
    fallback = reverse("ui:learner-home")
    if not candidate or not url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return fallback

    try:
        match = resolve(urlsplit(candidate).path)
    except Resolver404:
        return fallback
    predicate = SAFE_RETURN_ROUTES.get(match.view_name)
    if predicate is None or not predicate(user):
        return fallback
    return candidate
