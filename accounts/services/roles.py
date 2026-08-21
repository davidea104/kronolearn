"""Transactional content-role changes with append-only audit evidence."""

import logging
import uuid
from dataclasses import dataclass

from django.contrib.auth.models import Group
from django.db import transaction

from accounts.models import Account, RoleChangeLog
from accounts.security import CONTENT_ADMIN_ROLE, security_digest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoleChangeOutcome:
    result: str
    changed: bool
    actor_is_platform_admin: bool


def _record_outcome(
    *,
    actor,
    target,
    target_digest,
    action,
    result,
    changed,
    actor_is_platform_admin,
):
    RoleChangeLog.objects.create(
        actor=actor,
        target=target,
        requested_target_digest=target_digest,
        action=action,
        result=result,
        changed=changed,
    )
    event_suffix = {
        RoleChangeLog.Result.SUCCESS: "succeeded",
        RoleChangeLog.Result.DENIED: "denied",
        RoleChangeLog.Result.TARGET_NOT_FOUND: "target_not_found",
    }[result]
    extra = {
        "actor_id": str(actor.pk),
        "action": action,
        "result": result,
        "changed": changed,
    }
    if target_digest is not None:
        extra["target_digest"] = target_digest
    logger.info(f"accounts.role_change.{event_suffix}", extra=extra)
    return RoleChangeOutcome(
        result=result,
        changed=changed,
        actor_is_platform_admin=actor_is_platform_admin,
    )


@transaction.atomic
def change_content_role(actor, target_ref, action):
    if action not in RoleChangeLog.Action.values:
        raise ValueError("Unsupported content-role action.")

    requested_reference = str(target_ref)
    try:
        target_id = uuid.UUID(requested_reference)
    except (AttributeError, TypeError, ValueError):
        target_id = None

    account_ids = {actor.pk}
    if target_id is not None:
        account_ids.add(target_id)
    locked_accounts = {
        account.pk: account
        for account in Account.objects.select_for_update()
        .filter(pk__in=account_ids)
        .order_by("pk")
    }
    current_actor = locked_accounts[actor.pk]
    actor_is_platform_admin = bool(
        current_actor.is_active and current_actor.is_superuser
    )

    if target_id is None:
        return _record_outcome(
            actor=current_actor,
            target=None,
            target_digest=security_digest(
                requested_reference,
                purpose="role-target",
            ),
            action=action,
            result=RoleChangeLog.Result.TARGET_NOT_FOUND,
            changed=False,
            actor_is_platform_admin=actor_is_platform_admin,
        )

    target = locked_accounts.get(target_id)
    if target is None:
        return _record_outcome(
            actor=current_actor,
            target=None,
            target_digest=security_digest(str(target_id), purpose="role-target"),
            action=action,
            result=RoleChangeLog.Result.TARGET_NOT_FOUND,
            changed=False,
            actor_is_platform_admin=actor_is_platform_admin,
        )

    actor_is_authorized = actor_is_platform_admin and current_actor.pk != target.pk
    if not actor_is_authorized:
        return _record_outcome(
            actor=current_actor,
            target=target,
            target_digest=None,
            action=action,
            result=RoleChangeLog.Result.DENIED,
            changed=False,
            actor_is_platform_admin=actor_is_platform_admin,
        )

    content_group = Group.objects.get(name=CONTENT_ADMIN_ROLE)
    has_role = target.groups.filter(pk=content_group.pk).exists()
    changed = False
    if action == RoleChangeLog.Action.ASSIGN and not has_role:
        target.groups.add(content_group)
        changed = True
    elif action == RoleChangeLog.Action.REVOKE and has_role:
        target.groups.remove(content_group)
        changed = True

    return _record_outcome(
        actor=current_actor,
        target=target,
        target_digest=None,
        action=action,
        result=RoleChangeLog.Result.SUCCESS,
        changed=changed,
        actor_is_platform_admin=actor_is_platform_admin,
    )
