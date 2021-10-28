from typing import List

import graphene
from django.db import transaction, models
from django.db.models import QuerySet
from django.contrib.postgres.aggregates.general import ArrayAgg
from graphene_django import DjangoObjectType, DjangoListField
from graphene.types import generic
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.geo_scalars import PointScalar
from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import (
    DjangoPaginatedListObjectField,
    DateCountType,
    UserEntityCountType
)
from deep.permissions import ProjectPermissions as PP
from deep.serializers import URLCachedFileField

from lead.schema import Query as LeadQuery
from entry.schema import Query as EntryQuery
from export.schema import Query as ExportQuery
from geo.schema import RegionType, ProjectScopeQuery as GeoQuery
from quality_assurance.schema import Query as QualityAssuranceQuery

from lead.models import Lead
from entry.models import Entry
from geo.models import Region

from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectJoinRequest,
    ProjectOrganization,
    ProjectStats,
)
from .enums import (
    ProjectStatusEnum,
    ProjectJoinRequestStatusEnum,
    ProjectOrganizationTypeEnum,
    ProjectMembershipBadgeTypeEnum,
)

from .filter_set import (
    ProjectGqlFilterSet,
    ProjectMembershipGqlFilterSet,
    ProjectUserGroupMembershipGqlFilterSet,
)
from .activity import project_activity_log
from .tasks import generate_viz_stats


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
    leads_activity = graphene.List(graphene.NonNull(DateCountType))
    entries_activity = graphene.List(graphene.NonNull(DateCountType))

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

    organization_type = graphene.Field(ProjectOrganizationTypeEnum, required=True)
    organization_type_display = EnumDescription(source='get_organization_type_display', required=True)

    @staticmethod
    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root.organization_id)


class ProjectRoleType(DjangoObjectType):
    class Meta:
        model = ProjectRole
        only_fields = ('id', 'title', 'level')


class ProjectMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = ProjectMembership
        fields = (
            'id', 'member', 'linked_group',
            'role', 'joined_at', 'added_by',
        )

    badges = graphene.List(graphene.NonNull(ProjectMembershipBadgeTypeEnum))


class ProjectUserGroupMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = ProjectUserGroupMembership
        fields = (
            'id', 'usergroup',
            'role', 'joined_at', 'added_by',
        )

    badges = graphene.List(graphene.NonNull(ProjectMembershipBadgeTypeEnum))


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
    status = graphene.Field(ProjectStatusEnum, required=True)
    status_display = EnumDescription(source='get_status_display', required=True)
    organizations = graphene.List(graphene.NonNull(ProjectOrganizationType))
    has_analysis_framework = graphene.Boolean(required=True)
    has_assessment_template = graphene.Boolean(required=True)

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
    def resolve_has_analysis_framework(root, info):
        return root.analysis_framework_id is not None

    @staticmethod
    def resolve_has_assessment_template(root, info):
        return root.assessment_template_id is not None

    @staticmethod
    def resolve_current_user_role(root, info):
        return root.get_current_user_role(info.context.user)

    @staticmethod
    def resolve_allowed_permissions(root, info) -> List[PP.Permission]:
        return PP.get_permissions(root, info.context.request.user)

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


class ProjectMembershipListType(CustomDjangoListObjectType):
    class Meta:
        model = ProjectMembership
        filterset_class = ProjectMembershipGqlFilterSet


class ProjectUserGroupMembershipListType(CustomDjangoListObjectType):
    class Meta:
        model = ProjectUserGroupMembership
        filterset_class = ProjectUserGroupMembershipGqlFilterSet


class ProjectVizDataType(DjangoObjectType):
    class Meta:
        model = ProjectStats
        fields = (
            'modified_at',
            'status',
            'public_share',
        )

    data_url = graphene.String()
    public_url = graphene.String()

    @staticmethod
    def resolve_status(root, info, **_):
        if root.is_ready() or root.status == ProjectStats.Status.FAILURE:
            return root.status
        transaction.on_commit(lambda: generate_viz_stats.delay(root.project_id))
        # NOTE: Not changing modified_at if already pending
        if root.status != ProjectStats.Status.PENDING:
            root.status = ProjectStats.Status.PENDING
            root.save(update_fields=('status',))
        return root.status

    @staticmethod
    def resolve_data_url(root, info, **_):
        url = root.file
        if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
            url = root.confidential_file
        return url and info.context.request.build_absolute_uri(URLCachedFileField.name_to_representation(url))

    @staticmethod
    def resolve_public_url(root, info, **_):
        return root.get_public_url(info.context.request)


class ProjectDetailType(
    # -- Start --Project scopped entities
    LeadQuery,
    EntryQuery,
    ExportQuery,
    GeoQuery,
    QualityAssuranceQuery,
    # --  End  --Project scopped entities
    ProjectType,
):
    # NOTE: To avoid circular import
    from analysis_framework.schema import AnalysisFrameworkDetailType

    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id', 'title', 'description', 'start_date', 'end_date', 'analysis_framework',
            'category_editor', 'assessment_template', 'data',
            'is_default', 'is_private', 'is_visualization_enabled',
            'created_at', 'created_by',
            'modified_at', 'modified_by'
        )

    analysis_framework = graphene.Field(AnalysisFrameworkDetailType)
    activity_log = generic.GenericScalar()  # TODO: Need to define type
    top_sourcers = graphene.List(graphene.NonNull(UserEntityCountType))
    top_taggers = graphene.List(graphene.NonNull(UserEntityCountType))

    user_members = DjangoPaginatedListObjectField(
        ProjectMembershipListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    user_group_members = DjangoPaginatedListObjectField(
        ProjectUserGroupMembershipListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    is_visualization_available = graphene.Boolean(
        required=True,
        description='Checks if visualization is enabled and analysis framework is configured.',
    )
    viz_data = graphene.Field(ProjectVizDataType)

    @staticmethod
    def resolve_user_members(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return ProjectMembership.objects.filter(project=root).all()
        return []  # NOTE: Always return empty array FIXME: without empty everything is returned

    @staticmethod
    def resolve_user_group_members(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return ProjectUserGroupMembership.objects.filter(project=root).all()
        return []  # NOTE: Always return empty array FIXME: without empty everything is returned

    @staticmethod
    def resolve_activity_log(root, info, **kwargs):
        return list(project_activity_log(root))

    @staticmethod
    def resolve_top_sourcers(root, info, **kwargs):
        return get_top_entity_contributor(root, Lead)

    @staticmethod
    def resolve_top_taggers(root, info, **kwargs):
        return get_top_entity_contributor(root, Entry)

    @staticmethod
    def resolve_viz_data(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None and root.is_visualization_available:
            return root.project_stats


class ProjectByRegion(graphene.ObjectType):
    id = graphene.ID(required=True, description='Region\'s ID')
    projects_id = graphene.List(graphene.NonNull(graphene.ID))
    centroid = PointScalar()


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

    status = graphene.Field(ProjectJoinRequestStatusEnum, required=True)


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
    recent_projects = graphene.List(graphene.NonNull(ProjectDetailType))
    projects_by_region = graphene.List(graphene.NonNull(ProjectByRegion))

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

    @staticmethod
    def resolve_projects_by_region(root, info, **kwargs):
        # TODO: Cache this
        return Region.objects.filter(centroid__isnull=False).order_by('centroid').annotate(
            projects_id=ArrayAgg(
                'project',
                ordering='project',
                filter=models.Q(
                    project__in=Project.get_for_gq(info.context.user)
                )
            ),
        ).values('id', 'centroid', 'projects_id')
