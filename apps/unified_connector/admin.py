from django.contrib import admin

from .models import (
    UnifiedConnector,
    ConnectorSource,
    ConnectorSourceLead,
    ConnectorLead,
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
    pass
