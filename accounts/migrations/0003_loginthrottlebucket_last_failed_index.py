from typing import ClassVar

from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [
        ("accounts", "0002_seed_roles"),
    ]

    operations: ClassVar[list[object]] = [
        migrations.AddIndex(
            model_name="loginthrottlebucket",
            index=models.Index(
                fields=["last_failed_at"],
                name="acct_thr_failed_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="account",
            constraint=models.UniqueConstraint(
                Lower("email"),
                name="accounts_account_email_ci_unique",
            ),
        ),
    ]
