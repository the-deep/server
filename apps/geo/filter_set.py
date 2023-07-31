from functools import reduce

import django_filters
from django.db import models

from deep.filter_set import OrderEnumMixin
from utils.graphene.filters import (
    IDListFilter,
    StringListFilter,
    MultipleInputFilter,
)

from project.models import Project
from user_resource.filters import UserResourceFilterSet

from .models import (
    AdminLevel,
    GeoArea,
    Region,
)
from .enums import GeoAreaOrderingEnum


class GeoAreaFilterSet(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(
        label='Geo Area Label',
        method='geo_area_label'
    )

    class Meta:
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
                'extra': lambda _: {
                    'lookup_expr': 'icontains',
                },
            },
        }


# ------------------------------ Graphql filters -----------------------------------
class GeoAreaGqlFilterSet(OrderEnumMixin, django_filters.rest_framework.FilterSet):
    ids = IDListFilter(field_name='id')
    region_ids = IDListFilter(field_name='admin_level__region')
    admin_level_ids = IDListFilter(field_name='admin_level')
    search = django_filters.CharFilter(
        label='Geo Area Label search',
        method='geo_area_label'
    )
    titles = StringListFilter(
        label='Geo Area Label search (Multiple titles)',
        method='filter_titles'
    )
    ordering = MultipleInputFilter(GeoAreaOrderingEnum, method='ordering_filter')

    class Meta:
        model = GeoArea
        fields = ()

    def geo_area_label(self, queryset, _, value):
        if value:
            return queryset.filter(title__icontains=value)
        return queryset

    def filter_titles(self, queryset, _, values):
        if values:
            # Let's only use 20 max.
            _values = values[:20]
            return queryset.filter(
                reduce(
                    lambda acc, item: acc | item,
                    [
                        models.Q(title__icontains=value)
                        for value in _values
                    ]
                )
            )
        return queryset


class RegionGqlFilterSet(RegionFilterSet):
    search = django_filters.CharFilter(
        label='Region label search',
        method='region_search'
    )
    exclude_project = IDListFilter(method='exclude_project_region_filter')

    def region_search(self, queryset, _, value):
        if value:
            return queryset.filter(title__icontains=value)
        return queryset

    def exclude_project_region_filter(self, qs, name, value):
        if value:
            return qs.exclude(project__in=value).distinct()
        return qs
