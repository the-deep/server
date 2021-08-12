from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination


from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from geo.models import Region
from geo.filter_set import RegionFilterSet


def get_project_region_qs(info):
    return Region.objects.filter(project=info.context.active_project).distinct()


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
