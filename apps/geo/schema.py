import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.db import models

from utils.graphene.types import CustomDjangoListObjectType, FileFieldType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import NoOrderingPageGraphqlPagination

from geo.models import Region, GeoArea, AdminLevel
from geo.filter_set import RegionGqlFilterSet, GeoAreaGqlFilterSet


def get_users_region_qs(info):
    return Region.get_for(info.context.user).defer('geo_options')


def get_users_adminlevel_qs(info):
    # NOTE: We don't need geo_area_titles
    return AdminLevel.get_for(info.context.user).defer('geo_area_titles')


def get_geo_area_queryset_for_project_geo_area_type(queryset=None, defer_fields=('polygons', 'centroid', 'cached_data')):
    _queryset = queryset
    if _queryset is None:
        _queryset = GeoArea.objects
    _queryset = _queryset.annotate(
        region_title=models.F('admin_level__region__title'),
        admin_level_title=models.F('admin_level__title'),
        admin_level_level=models.F('admin_level__level'),
    )
    if defer_fields:
        _queryset = _queryset.defer(*defer_fields)
    return _queryset


class AdminLevelType(DjangoObjectType):
    class Meta:
        model = AdminLevel
        only_fields = (
            'id',
            'title', 'level', 'tolerance', 'stale_geo_areas', 'geo_shape_file',
            'name_prop', 'code_prop', 'parent_name_prop', 'parent_code_prop',
        )

    parent = graphene.ID(source='parent_id')
    geojson_file = graphene.Field(FileFieldType)
    bounds_file = graphene.Field(FileFieldType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_users_adminlevel_qs(info)


class RegionType(DjangoObjectType):
    class Meta:
        model = Region
        only_fields = (
            'id', 'title', 'public', 'regional_groups',
            'key_figures', 'population_data', 'media_sources',
            'centroid', 'is_published',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_users_region_qs(info)


class RegionDetailType(RegionType):
    class Meta:
        model = Region
        skip_registry = True
        only_fields = (
            'id', 'title', 'public', 'regional_groups',
            'key_figures', 'population_data', 'media_sources',
            'centroid', 'is_published',
        )

    admin_levels = graphene.List(graphene.NonNull(AdminLevelType))

    @staticmethod
    def resolve_admin_levels(root, info, **kwargs):
        return info.context.dl.geo.admin_levels_by_region.load(root.pk)


class RegionListType(CustomDjangoListObjectType):
    class Meta:
        model = Region
        filterset_class = RegionGqlFilterSet


class Query:
    region = DjangoObjectField(RegionDetailType)
    regions = DjangoPaginatedListObjectField(
        RegionListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_regions(root, info, **kwargs):
        return get_users_region_qs(info)


# -------------------------------- Project Specific Query ---------------------------------
# NOTE: Use with ProjectScopeQuery only.
class ProjectGeoAreaType(DjangoObjectType):
    class Meta:
        model = GeoArea
        only_fields = ('id', 'title',)
        skip_registry = True

    region_title = graphene.String(required=True)
    admin_level_title = graphene.String(required=True)
    admin_level_level = graphene.Int()
    parent_titles = graphene.List(graphene.NonNull(graphene.String), required=True)

    def resolve_parent_titles(root, info, **kwargs):
        return (root.cached_data or {}).get('parent_titles') or []


class ProjectGeoAreaListType(CustomDjangoListObjectType):
    class Meta:
        model = GeoArea
        base_type = ProjectGeoAreaType
        filterset_class = GeoAreaGqlFilterSet


class ProjectScopeQuery:
    geo_areas = DjangoPaginatedListObjectField(
        ProjectGeoAreaListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_geo_areas(queryset, info, **kwargs):
        return get_geo_area_queryset_for_project_geo_area_type(
            queryset=GeoArea.get_for_project(info.context.active_project)
        )
