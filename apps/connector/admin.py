from django.contrib import admin

from deep.admin import VersionAdmin
from connector.models import Connector


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    autocomplete_fields = ('created_by', 'modified_by',)
