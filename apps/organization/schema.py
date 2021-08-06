import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from gallery.schema import GalleryFileType
from gallery.models import File

from .models import Organization, OrganizationType as _OrganizationType
from .filters import OrganizationFilterSet


class OrganizationTypeType(DjangoObjectType):
    class Meta:
        model = _OrganizationType
        fields = (
            'id',
            'title',
            'short_name',
            'description',
        )


class OrganizationTypeListType(CustomDjangoListObjectType):
    class Meta:
        model = _OrganizationType
        filterset_class = []


class MergedAsOrganizationType(DjangoObjectType):
    class Meta:
        model = Organization
        skip_registry = True
        fields = (
            'id',
            'title',
            'logo',
        )
    logo = graphene.Field(GalleryFileType)

    def resolve_logo(root, info, **kwargs) -> File:
        return info.context.dl.organization.logo.load(root.pk)


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization
        fields = (
            'id',
            'title',
            'short_name',
            'long_name',
            'url',
            'logo',
            'regions',
            'organization_type',
            'verified',
        )
    logo = graphene.Field(GalleryFileType)
    merged_as = graphene.Field(MergedAsOrganizationType, source='parent')

    def resolve_logo(root, info, **kwargs) -> File:
        return info.context.dl.organization.logo.load(root.pk)


class OrganizationListType(CustomDjangoListObjectType):
    class Meta:
        model = Organization
        filterset_class = OrganizationFilterSet


class Query:
    organization = DjangoObjectField(OrganizationType)
    organizations = DjangoPaginatedListObjectField(
        OrganizationListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    organization_type = DjangoObjectField(OrganizationTypeType)
    organization_types = DjangoPaginatedListObjectField(
        OrganizationTypeListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
