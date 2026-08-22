"""Small deterministic factories for account-backed domain tests."""

from accounts.models import Account


def account_factory(**overrides) -> Account:
    email = overrides.pop("email", "factory-account@example.invalid")
    defaults = {
        "display_name": "Factory Account",
        "is_active": True,
        **overrides,
    }
    account, created = Account.objects.get_or_create(email=email, defaults=defaults)
    if created:
        account.set_unusable_password()
        account.save(update_fields=("password",))
    return account
