"""Managers for the custom account model."""

from django.contrib.auth.base_user import BaseUserManager

from accounts.security import canonicalize_account_email


class AccountManager(BaseUserManager):
    """Create accounts through the domain's canonical email representation."""

    use_in_migrations = True

    def normalize_email(self, email):
        return canonicalize_account_email(email)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        if not extra_fields.get("display_name"):
            raise ValueError("A display name is required.")

        account = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        account.set_password(password)
        account.save(using=self._db)
        return account

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)
