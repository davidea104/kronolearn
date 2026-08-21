"""Administrative views for accounts and immutable role-audit evidence."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Account, RoleChangeLog


@admin.register(Account)
class AccountAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "display_name", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "display_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("display_name",)}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "display_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(RoleChangeLog)
class RoleChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "actor",
        "target_reference",
        "action",
        "result",
        "changed",
    )
    list_display_links = None
    list_filter = ("action", "result", "changed")
    list_select_related = ("actor", "target")
    ordering = ("-occurred_at",)
    readonly_fields = (
        "id",
        "actor",
        "target",
        "requested_target_digest",
        "action",
        "result",
        "changed",
        "occurred_at",
    )
    fields = readonly_fields

    @admin.display(description="Objetivo")
    def target_reference(self, obj):
        if obj.target_id is not None:
            return f"Cuenta {obj.target_id}"
        return f"Referencia {obj.requested_target_digest[:12]}..."

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
