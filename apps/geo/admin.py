from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import Region, AdminLevel, GeoArea


class AdminLevelInline(admin.StackedInline):
    model = AdminLevel


@admin.register(Region)
class RegionAdmin(VersionAdmin):
    inlines = [AdminLevelInline]


class GeoAreaInline(admin.StackedInline):
    model = GeoArea


@admin.register(AdminLevel)
class AdminLevelAdmin(VersionAdmin):
    inlines = [GeoAreaInline]
