from typing import List

import graphene
from django.db import models
from django.db.models import QuerySet
from graphene_django import DjangoObjectType, DjangoListField
from graphene.types import generic
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import (
    DjangoPaginatedListObjectField,
    DateCountType,
    UserEntityCountType
)
from deep.permissions import ProjectPermissions as PP

from lead.schema import Query as LeadQuery
from entry.schema import Query as EntryQuery
from export.schema import Query as ExportQuery
from geo.schema import RegionType
from lead.models import Lead
from entry.models import Entry

from .models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectOrganization,
)
from .enums import (
    ProjectStatusEnum,
    ProjectJoinRequestStatusEnum,
    ProjectOrganizationTypeEnum,
)

from .filter_set import ProjectGqlFilterSet
from .activity import project_activity_log


def get_top_entity_contributor(project, Entity):
    contributors = ProjectMembership.objects.filter(
        project=project,
    ).annotate(
        entity_count=models.functions.Coalesce(models.Subquery(
            Entity.objects.filter(
                project=project,
                created_by=models.OuterRef('member'),
            ).order_by().values('project')
            .annotate(cnt=models.Count('*')).values('cnt')[:1],
            output_field=models.IntegerField(),
        ), 0),
    ).order_by('-entity_count').select_related('member', 'member__profile')[:5]

    return [
        {
            'id': contributor.id,
            'name': contributor.member.profile.get_display_name(),
            'user_id': contributor.member.id,
            'count': contributor.entity_count,
        } for contributor in contributors
    ]


class ProjectStatType(graphene.ObjectType):
    number_of_leads = graphene.Field(graphene.Int)
    number_of_leads_tagged = graphene.Field(graphene.Int)
    number_of_leads_tagged_and_controlled = graphene.Field(graphene.Int)
    number_of_entries = graphene.Field(graphene.Int)
    number_of_users = graphene.Field(graphene.Int)
    leads_activity = graphene.List(DateCountType)
    entries_activity = graphene.List(DateCountType)

    @staticmethod
    def resolve_leads_activity(root, info, **kwargs):
        return (root.stats_cache or {}).get('leads_activities') or []

    @staticmethod
    def resolve_entries_activity(root, info, **kwargs):
        return (root.stats_cache or {}).get('entries_activities') or []


class ProjectOrganizationType(DjangoObjectType):
    class Meta:
        model = ProjectOrganization
        fields = ('id', 'organization',)

    organization_type = graphene.Field(graphene.NonNull(ProjectOrganizationTypeEnum))

    @staticmethod
    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root.organization_id)


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = (
            'id', 'title', 'description', 'start_date', 'end_date',
            'analysis_framework', 'assessment_template',
            'is_default', 'is_private', 'is_visualization_enabled',
            'created_at', 'created_by',
            'modified_at', 'modified_by',
        )

    current_user_role = graphene.String()
    allowed_permissions = graphene.List(
        graphene.NonNull(
            graphene.Enum.from_enum(PP.Permission),
        ), required=True
    )
    stats = graphene.Field(ProjectStatType)
    membership_pending = graphene.Boolean(required=True)
    regions = DjangoListField(RegionType)
    status = graphene.Field(graphene.NonNull(ProjectStatusEnum))
    organizations = graphene.List(graphene.NonNull(ProjectOrganizationType))

    # NOTE: This is a custom feature
    # see: https://github.com/eamigo86/graphene-django-extras/compare/graphene-v2...the-deep:graphene-v2
    @staticmethod
    def get_custom_node(_, info, id):
        try:
            project = Project.get_for_gq(info.context.user).get(pk=id)
            info.context.set_active_project(project)
            return project
        except Project.DoesNotExist:
            return None

    @staticmethod
    def resolve_allowed_permissions(root, info) -> List[str]:
        return PP.get_permissions(
            root.get_current_user_role(info.context.request.user)
        )

    def resolve_stats(root, info, **kwargs):
        return info.context.dl.project.project_stat.load(root.pk)

    @staticmethod
    def resolve_membership_pending(root, info):
        return info.context.dl.project.join_status.load(root.pk)

    @staticmethod
    def resolve_organizations(root, info):
        return info.context.dl.project.organizations.load(root.pk)

    def resolve_regions(root, info, **kwargs):
        # NOTE: This is prefetched by graphene-django-extras
        return root.regions.all()


class AnalysisFrameworkVisibleProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id',
            'title',
            'is_private'
        )


class ProjectDetailType(
    # -- Start --Project scopped entities
    LeadQuery,
    EntryQuery,
    ExportQuery,
    # --  End  --Project scopped entities
    ProjectType,
):
    # NOTE: To avoid circular import
    from analysis_framework.schema import AnalysisFrameworkDetailType

    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id', 'title', 'description', 'start_date', 'end_date',
            'members', 'user_groups', 'analysis_framework',
            'category_editor', 'assessment_template', 'data',
            'is_default', 'is_private', 'is_visualization_enabled',
            'created_at', 'created_by',
            'modified_at', 'modified_by'
        )

    analysis_framework = graphene.Field(AnalysisFrameworkDetailType)
    activity_log = generic.GenericScalar()  # TODO: Need to define type
    top_sourcers = graphene.List(UserEntityCountType)
    top_taggers = graphene.List(UserEntityCountType)

    @staticmethod
    def resolve_activity_log(root, info, **kwargs):
        return list(project_activity_log(root))

    @staticmethod
    def resolve_top_sourcers(root, info, **kwargs):
        return get_top_entity_contributor(root, Lead)

    @staticmethod
    def resolve_top_taggers(root, info, **kwargs):
        return get_top_entity_contributor(root, Entry)


class ProjectJoinRequestType(DjangoObjectType):
    class Meta:
        model = ProjectJoinRequest
        fields = (
            'id',
            'data',
            'requested_by',
            'responded_by',
            'project',
        )

    status = graphene.Field(graphene.NonNull(ProjectJoinRequestStatusEnum))


class ProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        filterset_class = ProjectGqlFilterSet


class Query:
    project = DjangoObjectField(ProjectDetailType)
    projects = DjangoPaginatedListObjectField(
        ProjectListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    recent_projects = graphene.List(ProjectDetailType)

    # NOTE: This is a custom feature, see https://github.com/the-deep/graphene-django-extras
    # see: https://github.com/eamigo86/graphene-django-extras/compare/graphene-v2...the-deep:graphene-v2

    @staticmethod
    def resolve_projects(root, info, **kwargs) -> QuerySet:
        return Project.get_for_gq(info.context.user).distinct()

    @staticmethod
    def resolve_recent_projects(root, info, **kwargs) -> QuerySet:
        # only the recent project of the user member of
        queryset = Project.get_for_gq(info.context.user, only_member=True)
        return Project.get_recent_active_projects(info.context.user, queryset)
