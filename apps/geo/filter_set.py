import django_filters
from django.db import models

from geo.models import (
    AdminLevel,
    GeoArea,
    Region,
)
from project.models import Project
from user_resource.filters import UserResourceFilterSet


class GeoAreaFilterSet(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(
        label='Geo Area Label',
        method='geo_area_label'
    )

    class Meat:
        model = GeoArea
        fields = ()

    def geo_area_label(self, queryset, name, value):
        if value:
            return queryset.filter(label__icontains=value)
        return queryset


class RegionFilterSet(UserResourceFilterSet):
    """
    Region filter set

    Filter by code, title and public fields
    """
    # NOTE: This filter the regions not in the supplied project
    exclude_project = django_filters.ModelMultipleChoiceFilter(
        method='exclude_project_region_filter',
        widget=django_filters.widgets.CSVWidget,
        queryset=Project.objects.all(),
    )

    class Meta:
        model = Region
        fields = ['id', 'code', 'title', 'public', 'project',
                  'created_at', 'created_by', 'modified_at', 'modified_by']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    def exclude_project_region_filter(self, qs, name, value):
        if value:
            return qs.exclude(project__in=value).distinct()
        return qs


class AdminLevelFilterSet(django_filters.rest_framework.FilterSet):
    """
    AdminLevel filter set

    Filter by title, region and parent
    """
    class Meta:
        model = AdminLevel
        fields = ['id', 'title', 'region', 'parent']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
