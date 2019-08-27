from django.contrib import admin
from reversion.admin import VersionAdmin
from connector.models import Connector, EMMEntity


@admin.register(Connector)
class ConnectorAdmin(VersionAdmin):
    pass


@admin.register(EMMEntity)
class EMMEntityAdmin(admin.ModelAdmin):
    pass
