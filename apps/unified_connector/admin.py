from django.contrib import admin

from .models import (
    ConnectorLead,
    ConnectorSource,
    ConnectorSourceLead,
    UnifiedConnector,
)


@admin.register(UnifiedConnector)
class UnifiedConnectorAdmin(admin.ModelAdmin):
    pass


@admin.register(ConnectorSource)
class ConnectorSourceAdmin(admin.ModelAdmin):
    pass


@admin.register(ConnectorSourceLead)
class ConnectorSourceLeadAdmin(admin.ModelAdmin):
    pass


@admin.register(ConnectorLead)
class ConnectorLeadAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "created_at",
        "modified_at",
    ]
    readonly_fields = (
        "created_at",
        "modified_at",
    )
    autocomplete_fields = (
        "authors",
        "source",
    )
    search_fields = ("title",)
