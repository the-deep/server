from django.contrib import admin
from django.db.models import Count
from admin_auto_filters.filters import AutocompleteFilterFactory

from deep.admin import VersionAdmin
from connector.models import (
    Connector,
    EMMConfig,
    ConnectorSource,

    UnifiedConnector,
    UnifiedConnectorSource,
    ConnectorLead,
)


admin.site.register(ConnectorSource)


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    autocomplete_fields = ('created_by', 'modified_by',)


@admin.register(EMMConfig)
class EMMConfigAdmin(VersionAdmin):
    list_display = ('entity_tag', 'trigger_tag', 'trigger_attribute',)


# ------------------------------------- UNIFIED CONNECTOR -------------------------------------- #

class UnifiedConnectorSourceAdmin(admin.StackedInline):
    model = UnifiedConnectorSource
    extra = 0


@admin.register(UnifiedConnector)
class UnifiedConnectorAdmin(VersionAdmin):
    list_display = ('title', 'project', 'get_sources_count')
    list_filter = [
        AutocompleteFilterFactory('Project', 'project'),
        AutocompleteFilterFactory('Created by', 'created_by'),
        'created_at',
    ]
    autocomplete_fields = ('project', 'created_by', 'modified_by',)
    inlines = [UnifiedConnectorSourceAdmin]

    def get_queryset(self, request):
        view_name = request.resolver_match.view_name
        qs = super().get_queryset(request)
        if view_name.endswith('_changelist'):
            return qs.annotate(sources_count=Count('unifiedconnectorsource'))
        elif view_name.endswith('_change'):
            return qs.prefetch_related('unifiedconnectorsource_set')
        return qs

    def get_sources_count(self, obj):
        return obj.sources_count
    get_sources_count.short_description = 'Source count'


@admin.register(ConnectorLead)
class ConnectorLeadAdmin(admin.ModelAdmin):
    list_display = ('url', 'status')
    list_filter = ('status',)
