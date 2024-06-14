from connector.models import Connector, ConnectorSource, EMMConfig
from django.contrib import admin

from deep.admin import VersionAdmin


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    autocomplete_fields = (
        "created_by",
        "modified_by",
    )


@admin.register(EMMConfig)
class EMMConfigAdmin(VersionAdmin):
    list_display = (
        "entity_tag",
        "trigger_tag",
        "trigger_attribute",
    )


admin.site.register(ConnectorSource)
