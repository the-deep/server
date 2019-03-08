from django.contrib import admin
from reversion.admin import VersionAdmin
from connector.models import Connector


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    pass
