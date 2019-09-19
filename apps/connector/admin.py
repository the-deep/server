from django.contrib import admin

from deep.admin import VersionAdmin
from connector.models import Connector, EMMConfig


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    autocomplete_fields = ('created_by', 'modified_by',)


@admin.register(EMMConfig)
class EMMConfigAdmin(VersionAdmin):
    pass
