"""Authorized account lookups for cross-domain consumers."""

import uuid

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.transaction import TransactionManagementError

from accounts.models import Account
from accounts.security import CONTENT_ADMIN_ROLE

_CONTENT_ADMIN_DENIED = "Content administrator access denied."


def resolve_content_admin(actor_ref: str, *, for_update: bool = False) -> Account:
    """Return an active content administrator without exposing account details."""
    if for_update and not transaction.get_connection().in_atomic_block:
        raise TransactionManagementError(
            "A transaction is required to lock the content administrator."
        )

    try:
        actor_id = uuid.UUID(str(actor_ref))
    except (AttributeError, TypeError, ValueError):
        raise PermissionDenied(_CONTENT_ADMIN_DENIED) from None

    accounts = Account.objects
    if for_update:
        accounts = accounts.select_for_update()
    account = accounts.filter(pk=actor_id).first()
    if (
        account is None
        or not account.is_active
        or not account.groups.filter(name=CONTENT_ADMIN_ROLE).exists()
    ):
        raise PermissionDenied(_CONTENT_ADMIN_DENIED)
    return account
