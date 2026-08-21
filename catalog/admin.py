"""Read-only administration for published catalog history."""

from django.contrib import admin

from catalog.models import CatalogChangeLog, ModuleVersion, TrackVersion


class ReadOnlyHistoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TrackVersion)
class TrackVersionAdmin(ReadOnlyHistoryAdmin):
    list_display = ("track", "version_number", "author", "published_at")
    readonly_fields = tuple(field.name for field in TrackVersion._meta.fields)


@admin.register(ModuleVersion)
class ModuleVersionAdmin(ReadOnlyHistoryAdmin):
    list_display = ("module", "version_number", "author", "published_at")
    readonly_fields = tuple(field.name for field in ModuleVersion._meta.fields)


@admin.register(CatalogChangeLog)
class CatalogChangeLogAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "occurred_at",
        "actor",
        "entity_type",
        "action",
        "result",
        "changed",
    )
    readonly_fields = tuple(field.name for field in CatalogChangeLog._meta.fields)
