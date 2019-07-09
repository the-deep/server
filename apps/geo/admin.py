from django.contrib import admin
from django.contrib import messages

from deep.admin import VersionAdmin, linkify

from .models import Region, AdminLevel, GeoArea
from .tasks import cal_region_cache, cal_admin_level_cache


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


def trigger_admin_level_cache_reset(modeladmin, request, queryset):
    cal_admin_level_cache.delay(
        list(queryset.values_list('id', flat=True).distinct())
    )
    messages.add_message(
        request, messages.INFO,
        'Successfully triggered Admin Levels: ' + ', '.join(
            '{}(level={}):pk={}'.format(*value)
            for value in queryset.values_list('title', 'level', 'id').distinct()
        )
    )


trigger_admin_level_cache_reset.short_description = 'Trigger cache reset for selected AdminLevels'


class AdminLevelInline(admin.StackedInline):
    model = AdminLevel
    raw_id_fields = ('parent', 'region', 'geo_shape_file',)
    exclude = ('geojson', 'bounds', 'geo_area_titles',)
    max_num = 0


@admin.register(Region)
class RegionAdmin(VersionAdmin):
    list_display = ('title', 'project_count')
    search_fields = ('title',)
    inlines = [AdminLevelInline]
    exclude = ('geo_options',)
    actions = [trigger_region_cache_reset]
    list_per_page = 10

    def project_count(self, instance):
        return instance.project_set.count()


@admin.register(AdminLevel)
class AdminLevelAdmin(VersionAdmin):
    search_fields = ('title', 'region__title',)
    list_display = ('title', linkify('region'),)
    raw_id_fields = AdminLevelInline.raw_id_fields
    exclude = ('geojson', 'bounds', 'geo_area_titles',)
    actions = [trigger_admin_level_cache_reset]
    list_per_page = 10


@admin.register(GeoArea)
class GeoAreaAdmin(VersionAdmin):
    search_fields = ('title',)
    list_display = ('title', linkify('admin_level'), linkify('parent'), 'code',)
    raw_id_fields = ('parent', 'admin_level',)
    list_per_page = 10
