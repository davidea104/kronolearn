"""Transactional public-account registration."""

from django.contrib.auth.models import Group
from django.db import transaction

from accounts.models import Account
from accounts.security import LEARNER_ROLE


@transaction.atomic
def register_account(*, email: str, display_name: str, password: str) -> Account:
    """Create one active learner or roll the entire registration back."""
    account = Account.objects.create_user(
        email=email,
        display_name=display_name,
        password=password,
    )
    learner_group = Group.objects.get(name=LEARNER_ROLE)
    account.groups.add(learner_group)
    return account
