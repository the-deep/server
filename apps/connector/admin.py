from django.contrib import admin

from deep.admin import VersionAdmin
from connector.models import Connector, EMMConfig, ConnectorSource


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    autocomplete_fields = ('created_by', 'modified_by',)


@admin.register(EMMConfig)
class EMMConfigAdmin(VersionAdmin):
    list_display = ('entity_tag', 'trigger_tag', 'trigger_attribute',)


admin.site.register(ConnectorSource)
