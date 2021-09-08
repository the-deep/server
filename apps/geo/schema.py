import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.db import models

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from geo.models import Region, GeoArea
from geo.filter_set import RegionFilterSet, GeoAreaGqlFilterSet


def get_project_region_qs(info):
    return Region.objects.filter(project=info.context.active_project).distinct()


def get_geo_area_queryset_for_project_geo_area_type():
    return GeoArea.objects.annotate(
        region_title=models.F('admin_level__region__title'),
        admin_level_title=models.F('admin_level__title'),
    )


class RegionType(DjangoObjectType):
    class Meta:
        model = Region
        fields = (
            'id', 'title', 'public', 'regional_groups',
            'key_figures', 'population_data', 'media_sources',
            'geo_options'
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_project_region_qs(info)


class RegionListType(CustomDjangoListObjectType):
    class Meta:
        model = Region
        filterset_class = RegionFilterSet


class Query:
    region = DjangoObjectField(RegionType)
    regions = DjangoPaginatedListObjectField(
        RegionListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_regions(queryset, info, **kwargs):
        return get_project_region_qs(info)


# -------------------------------- Project Specific Query ---------------------------------
# NOTE: Use with ProjectScopeQuery only.
class ProjectGeoAreaType(DjangoObjectType):
    class Meta:
        model = GeoArea
        fields = ('id', 'title',)
        skip_registry = True

    region_title = graphene.String(required=True)
    admin_level_title = graphene.String(required=True)


class ProjectGeoAreaListType(CustomDjangoListObjectType):
    class Meta:
        model = GeoArea
        base_type = ProjectGeoAreaType
        filterset_class = GeoAreaGqlFilterSet


class ProjectScopeQuery:
    geo_areas = DjangoPaginatedListObjectField(
        ProjectGeoAreaListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_geo_areas(queryset, info, **kwargs):
        return get_geo_area_queryset_for_project_geo_area_type().filter(
            admin_level__region__project=info.context.active_project,
        )
