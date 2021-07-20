import graphene
from graphene_django import DjangoObjectType

from gallery.schema import GalleryFileType
from gallery.models import File

from .models import Organization, OrganizationType as _OrganizationType


class OrganizationTypeType(DjangoObjectType):
    class Meta:
        model = _OrganizationType
        fields = (
            'id',
            'title',
            'short_name',
            'description',
        )


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
