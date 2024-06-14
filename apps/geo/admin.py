from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from deep.admin import VersionAdmin, linkify

from .models import AdminLevel, GeoArea, Region
from .tasks import cal_admin_level_cache, cal_region_cache


def trigger_region_cache_reset(_, request, queryset):
    cal_region_cache.delay(list(queryset.values_list("id", flat=True).distinct()))
    messages.add_message(
        request,
        messages.INFO,
        mark_safe(
            "Successfully triggered regions: <br><hr>"
            + "<br>".join("* {0} : ({1}) {2}".format(*value) for value in queryset.values_list("id", "code", "title").distinct())
        ),
    )


trigger_region_cache_reset.short_description = "Trigger cache reset for selected Regions"


def trigger_admin_level_cache_reset(_, request, queryset):
    cal_admin_level_cache.delay(list(queryset.values_list("id", flat=True).distinct()))
    messages.add_message(
        request,
        messages.INFO,
        mark_safe(
            "Successfully triggered Admin Levels: <br><hr>"
            + "<br>".join(
                "* {0} : (level={1}) {2}".format(*value) for value in queryset.values_list("id", "level", "title").distinct()
            )
        ),
    )


trigger_admin_level_cache_reset.short_description = "Trigger cache reset for selected AdminLevels"


class AdminLevelInline(admin.StackedInline):
    model = AdminLevel
    autocomplete_fields = (
        "parent",
        "geo_shape_file",
    )
    exclude = ("geo_area_titles",)
    max_num = 0


@admin.register(Region)
class RegionAdmin(VersionAdmin):
    list_display = ("title", "project_count")
    search_fields = ("title",)
    inlines = [AdminLevelInline]
    exclude = ("geo_options",)
    actions = [trigger_region_cache_reset]
    autocomplete_fields = ("created_by", "modified_by")
    list_per_page = 10

    def project_count(self, instance):
        return instance.project_set.count()


@admin.register(AdminLevel)
class AdminLevelAdmin(VersionAdmin):
    search_fields = (
        "title",
        "region__title",
    )
    list_display = (
        "title",
        linkify("region"),
    )
    autocomplete_fields = ("region",) + AdminLevelInline.autocomplete_fields
    exclude = ("geo_area_titles",)
    actions = [trigger_admin_level_cache_reset]
    list_per_page = 10


@admin.register(GeoArea)
class GeoAreaAdmin(VersionAdmin):
    search_fields = ("title",)
    list_display = (
        "title",
        linkify("admin_level"),
        linkify("parent"),
        "code",
    )
    autocomplete_fields = (
        "parent",
        "admin_level",
    )
    list_per_page = 10
