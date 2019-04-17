from django.contrib import admin
from reversion.admin import VersionAdmin
from django.contrib import messages

from .models import Region, AdminLevel, GeoArea
from .tasks import cal_region_cache


def trigger_region_cache_reset(modeladmin, request, queryset):
    cal_region_cache.delay(
        list(queryset.values_list('id', flat=True).distinct())
    )
    messages.add_message(
        request, messages.INFO,
        'Successfully triggered regions: ' + ', '.join(
            '{}({}):pk={}'.format(*value)
            for value in queryset.values_list('title', 'code', 'id').distinct()
        )
    )


trigger_region_cache_reset.short_description = 'Trigger cache reset for selected Regions'


class AdminLevelInline(admin.StackedInline):
    model = AdminLevel
    exclude = ('geojson', 'bounds', 'geo_area_titles',)
    max_num = 0


class GeoAreaInline(admin.StackedInline):
    model = GeoArea
    exclude = ('ploygons', 'data',)
    max_num = 0


@admin.register(Region)
class RegionAdmin(VersionAdmin):
    search_fields = ('title',)
    inlines = [AdminLevelInline]
    exclude = ('geo_options',)
    actions = [trigger_region_cache_reset]


@admin.register(AdminLevel)
class AdminLevelAdmin(VersionAdmin):
    search_fields = ('title',)
    inlines = [GeoAreaInline]
    exclude = ('geojson', 'bounds', 'geo_area_titles',)
