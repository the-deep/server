import graphene

from graphene_django import DjangoObjectType, DjangoListField

from utils.graphene.types import CustomDjangoListObjectType

from analysis_framework.models import AnalysisFramework
from geo.models import Region

from .models import Project, ProjectOrganization
from .filter_set import ProjectGqlFilterSet


class PublicProjectStatType(graphene.ObjectType):
    number_of_leads = graphene.Field(graphene.Int)
    number_of_users = graphene.Field(graphene.Int)


class PublicProjectOrganizationType(DjangoObjectType):
    class Meta:
        model = ProjectOrganization
        skip_registry = True
        fields = ('id', 'organization',)

    @staticmethod
    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root.organization_id)


class PublicProjectRegionType(DjangoObjectType):
    class Meta:
        model = Region
        skip_registry = True
        fields = (
            'id', 'title'
        )


class PublicProjectAnalysisFrameworkForType(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        skip_registry = True
        fields = (
            'id', 'title'
        )


class PublicProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id', 'description', 'title',
            'created_at'
        )
    stats = graphene.Field(PublicProjectStatType)
    regions = DjangoListField(PublicProjectRegionType)
    organizations = graphene.List(graphene.NonNull(PublicProjectOrganizationType))
    analysis_framework = graphene.Field(PublicProjectAnalysisFrameworkForType)

    @staticmethod
    def resolve_organizations(root, info):
        return info.context.dl.project.organizations.load(root.pk)

    def resolve_regions(root, info, **kwargs):
        return info.context.dl.project.public_geo_region.load(root.pk)

    def resolve_stats(root, info, **kwargs):
        return info.context.dl.project.project_stat.load(root.pk)


class PublicProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        base_type = PublicProjectType
        filterset_class = ProjectGqlFilterSet
