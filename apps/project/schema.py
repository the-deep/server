from typing import List

import graphene
from django.db import transaction, models
from django.db.models import QuerySet
from graphene_django import DjangoObjectType, DjangoListField
from graphene.types import generic
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.geo_scalars import PointScalar
from utils.graphene.enums import EnumDescription
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.types import (
    CustomDjangoListObjectType,
    ClientIdMixin,
    DateCountType,
    UserEntityCountType,
    UserEntityDateType,
)
from utils.graphene.fields import (
    DjangoPaginatedListObjectField,
)
from deep.permissions import ProjectPermissions as PP
from deep.serializers import URLCachedFileField
from user_resource.schema import UserResourceMixin

from user.models import User
from user.schema import UserType
from lead.schema import Query as LeadQuery
from entry.schema import Query as EntryQuery
from export.schema import Query as ExportQuery
from geo.schema import RegionDetailType, ProjectScopeQuery as GeoQuery
from quality_assurance.schema import Query as QualityAssuranceQuery
from ary.schema import Query as AryQuery
from analysis.schema import Query as AnalysisQuery
from unified_connector.schema import UnifiedConnectorQueryType
from assisted_tagging.schema import AssistedTaggingQueryType

from lead.models import Lead
from entry.models import Entry
from geo.models import Region

from lead.filter_set import LeadsFilterDataInputType

from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectJoinRequest,
    ProjectOrganization,
    ProjectStats,
    RecentActivityType as ActivityTypes,
)
from .enums import (
    ProjectPermissionEnum,
    ProjectStatusEnum,
    ProjectRoleTypeEnum,
    ProjectJoinRequestStatusEnum,
    ProjectOrganizationTypeEnum,
    ProjectMembershipBadgeTypeEnum,
    RecentActivityTypeEnum,
)

from .filter_set import (
    ProjectGqlFilterSet,
    ProjectMembershipGqlFilterSet,
    ProjectUserGroupMembershipGqlFilterSet,
    ProjectByRegionGqlFilterSet,
    PublicProjectByRegionGqlFileterSet,
)
from .activity import project_activity_log
from .tasks import generate_viz_stats, get_project_stats
from .public_schema import PublicProjectListType
from organization.models import Organization
from organization.schema import OrganizationType
from analysis_framework.models import AnalysisFramework


def get_recent_active_users(project, max_users=3):
    # id, date
    users_activity = project.get_recent_active_users_id_and_date(max_users=max_users)
    recent_active_users_map = {
        user.pk: user
        for user in User.objects.filter(pk__in=[id for id, _ in users_activity])
    }
    recent_active_users = [
        (recent_active_users_map[id], date)
        for id, date in users_activity
        if id in recent_active_users_map
    ]
    return [
        {
            'id': user.id,
            'name': user.get_display_name(),
            'date': date,
        } for user, date in recent_active_users
    ]


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
    ).order_by('-entity_count').select_related('member')[:5]

    return [
        {
            'id': contributor.id,
            'name': contributor.member.get_display_name(),
            'user_id': contributor.member.id,
            'count': contributor.entity_count,
        } for contributor in contributors
    ]


class ExploreStastOrganizationType(OrganizationType):
    class Meta:
        model = Organization
        skip_registry = True
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
    source_count = graphene.Int()
    project_count = graphene.Int()


class ExploreDashboardStatType(graphene.ObjectType):
    total_projects = graphene.Int()
    total_registered_users = graphene.Int()
    total_leads = graphene.Int()
    total_entries = graphene.Int()
    total_active_users = graphene.Int()
    total_authors = graphene.Int()
    total_publishers = graphene.Int()

    top_ten_authors = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_sources = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_frameworks = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopActiveFrameworksType', (graphene.ObjectType,), {
                'analysis_framework_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'analysis_framework_title': graphene.String(),
                'project_count': graphene.NonNull(graphene.Int),
                'entry_count': graphene.NonNull(graphene.Int)
            })
        )
    )
    top_ten_project_users = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopProjectType', (graphene.ObjectType,), {
                'project_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'project_title': graphene.String(),
                'user_count': graphene.NonNull(graphene.Int),
            })
        )
    )
    top_ten_project_entries = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopProjectEntryType', (graphene.ObjectType,), {
                'project_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'project_title': graphene.String(),
                'source_count': graphene.NonNull(graphene.Int),
                'entry_count': graphene.NonNull(graphene.Int),
            })
        )
    )


class ProjectExploreStatType(graphene.ObjectType):
    calculated_at = graphene.DateTime()
    total_projects = graphene.Int()
    total_users = graphene.Int()
    total_leads = graphene.Int()
    total_entries = graphene.Int()
    leads_added_weekly = graphene.Int()
    daily_average_leads_tagged_per_project = graphene.Float()
    generated_exports_monthly = graphene.Int()
    top_active_projects = graphene.List(
        graphene.NonNull(
            type('ExploreProjectStatTopActiveProjectsType', (graphene.ObjectType,), {
                'project_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'project_title': graphene.String(),
                'analysis_framework_id': graphene.ID(),
                'analysis_framework_title': graphene.String(),
            })
        )
    )
    top_active_frameworks = graphene.List(
        graphene.NonNull(
            type('ExploreProjectStatTopActiveFrameworksType', (graphene.ObjectType,), {
                'analysis_framework_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'analysis_framework_title': graphene.String(),
                'project_count': graphene.NonNull(graphene.Int),
                'source_count': graphene.NonNull(graphene.Int)
            })
        )
    )


class ProjectStatType(graphene.ObjectType):
    number_of_leads = graphene.Field(graphene.Int)
    number_of_leads_not_tagged = graphene.Field(graphene.Int)
    number_of_leads_in_progress = graphene.Field(graphene.Int)
    number_of_leads_tagged = graphene.Field(graphene.Int)
    number_of_entries = graphene.Field(graphene.Int)
    number_of_entries_verified = graphene.Field(graphene.Int)
    number_of_entries_controlled = graphene.Field(graphene.Int)
    number_of_users = graphene.Field(graphene.Int)
    leads_activity = graphene.List(graphene.NonNull(DateCountType))
    entries_activity = graphene.List(graphene.NonNull(DateCountType))

    # With Filter
    filtered_number_of_leads = graphene.Field(graphene.Int)
    filtered_number_of_leads_not_tagged = graphene.Field(graphene.Int)
    filtered_number_of_leads_in_progress = graphene.Field(graphene.Int)
    filtered_number_of_leads_tagged = graphene.Field(graphene.Int)
    filtered_number_of_entries = graphene.Field(graphene.Int)
    filtered_number_of_entries_verified = graphene.Field(graphene.Int)
    filtered_number_of_entries_controlled = graphene.Field(graphene.Int)

    @staticmethod
    def resolve_leads_activity(root, info, **kwargs):
        return (root.stats_cache or {}).get('leads_activities') or []

    @staticmethod
    def resolve_entries_activity(root, info, **kwargs):
        return (root.stats_cache or {}).get('entries_activities') or []


class ProjectOrganizationType(DjangoObjectType):
    class Meta:
        model = ProjectOrganization
        only_fields = ('id', 'organization',)

    organization_type = graphene.Field(ProjectOrganizationTypeEnum, required=True)
    organization_type_display = EnumDescription(source='get_organization_type_display', required=True)

    @staticmethod
    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root.organization_id)


class ProjectRoleType(DjangoObjectType):
    class Meta:
        model = ProjectRole
        only_fields = ('id', 'title', 'level')

    type = graphene.Field(ProjectRoleTypeEnum, required=True)


class ProjectMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = ProjectMembership
        only_fields = (
            'id', 'member', 'linked_group',
            'role', 'joined_at', 'added_by',
        )

    badges = graphene.List(graphene.NonNull(ProjectMembershipBadgeTypeEnum))


class ProjectUserGroupMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = ProjectUserGroupMembership
        only_fields = (
            'id', 'usergroup',
            'role', 'joined_at', 'added_by',
        )

    badges = graphene.List(graphene.NonNull(ProjectMembershipBadgeTypeEnum))


class ProjectType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = Project
        only_fields = (
            'id', 'title', 'description', 'start_date', 'end_date',
            'analysis_framework', 'assessment_template',
            'is_default', 'is_private', 'is_test', 'is_visualization_enabled',
            'created_at', 'created_by',
            'modified_at', 'modified_by',
        )

    current_user_role = graphene.Field(ProjectRoleTypeEnum)
    allowed_permissions = graphene.List(
        graphene.NonNull(
            ProjectPermissionEnum,
        ), required=True
    )
    stats = graphene.Field(ProjectStatType)
    membership_pending = graphene.Boolean(required=True)
    is_rejected = graphene.Boolean(required=True)
    regions = DjangoListField(RegionDetailType)
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

    @staticmethod
    def resolve_stats(root, info):
        return info.context.dl.project.project_stat.load(root.pk)

    @staticmethod
    def resolve_membership_pending(root, info):
        return info.context.dl.project.join_status.load(root.pk)

    @staticmethod
    def resolve_is_rejected(root, info):
        return info.context.dl.project.project_rejected_status.load(root.pk)

    @staticmethod
    def resolve_organizations(root, info):
        return info.context.dl.project.organizations.load(root.pk)

    def resolve_regions(root, info, **kwargs):
        # Need to have a base permission
        if PP.check_permission(info, PP.Permission.BASE_ACCESS):
            return info.context.dl.project.geo_region.load(root.pk)
        return info.context.dl.project.public_geo_region.load(root.pk)


class RecentActivityType(graphene.ObjectType):
    id = graphene.ID(required=True)
    created_at = graphene.DateTime()
    project = graphene.Field(ProjectType)
    created_by = graphene.Field(UserType)
    type = graphene.Field(RecentActivityTypeEnum, required=True)
    type_display = EnumDescription(required=True)
    lead_id = graphene.ID(required=True)
    entry_id = graphene.ID()

    def resolve_created_by(root, info, **kwargs):
        id = int(root['created_by'])
        return info.context.dl.project.users.load(id)

    def resolve_project(root, info, **kwargs):
        id = int(root['project'])
        return info.context.dl.project.projects.load(id)

    def resolve_type_display(root, info, **kwargs):
        return ActivityTypes(root['type']).label

    def resolve_entry_id(root, info, **kwargs):
        if root['type'] == ActivityTypes.LEAD:
            return
        return root['entry_id']


class AnalysisFrameworkVisibleProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        only_fields = (
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
        only_fields = (
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
    AryQuery,
    AnalysisQuery,
    # --  End  --Project scopped entities
    ProjectType,
):
    # NOTE: To avoid circular import
    from analysis_framework.schema import AnalysisFrameworkDetailType

    class Meta:
        model = Project
        skip_registry = True
        only_fields = (
            'id', 'title', 'description', 'start_date', 'end_date', 'analysis_framework',
            'category_editor', 'assessment_template', 'data',
            'created_at', 'created_by',
            'modified_at', 'modified_by',
            'is_default', 'is_private', 'is_test', 'is_visualization_enabled',
            'has_publicly_viewable_unprotected_leads',
            'has_publicly_viewable_restricted_leads',
            'has_publicly_viewable_confidential_leads',
        )

    analysis_framework = graphene.Field(AnalysisFrameworkDetailType)
    activity_log = generic.GenericScalar()  # TODO: Need to define type
    recent_active_users = graphene.List(graphene.NonNull(UserEntityDateType))
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
    stats = graphene.Field(
        ProjectStatType,
        filters=LeadsFilterDataInputType(),
    )
    viz_data = graphene.Field(ProjectVizDataType)
    # Other scoped queries
    unified_connector = graphene.Field(UnifiedConnectorQueryType)
    assisted_tagging = graphene.Field(AssistedTaggingQueryType)

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
    def resolve_recent_active_users(root, info, **kwargs):
        return get_recent_active_users(root)

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

    @staticmethod
    def resolve_stats(root, info, filters=None):
        if root.get_current_user_role(info.context.request.user) is not None:
            return get_project_stats(root, info, filters)

    @staticmethod
    def resolve_unified_connector(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return {}

    @staticmethod
    def resolve_assisted_tagging(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return {}


class ProjectByRegion(graphene.ObjectType):
    id = graphene.ID(required=True, description='Region\'s ID')
    # NOTE: Annotated by ProjectByRegionGqlFilterSet/PublicProjectByRegionGqlFileterSet
    projects_id = graphene.List(graphene.NonNull(graphene.ID))
    centroid = PointScalar()


class ProjectJoinRequestType(DjangoObjectType):
    class Meta:
        model = ProjectJoinRequest
        only_fields = (
            'id',
            'data',
            'requested_by',
            'responded_by',
            'project',
        )

    status = graphene.Field(ProjectJoinRequestStatusEnum, required=True)


class RegionWithProject(DjangoObjectType):
    class Meta:
        model = Region
        only_fields = (
            'id', 'centroid',
        )
    # NOTE: Annotated by ProjectByRegionGqlFilterSet/PublicProjectByRegionGqlFileterSet
    projects_id = graphene.List(graphene.NonNull(graphene.ID))


class ProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        filterset_class = ProjectGqlFilterSet


class ProjectByRegionListType(CustomDjangoListObjectType):
    class Meta:
        model = Region
        base_type = RegionWithProject
        filterset_class = ProjectByRegionGqlFilterSet


class PublicProjectByRegionListType(CustomDjangoListObjectType):
    class Meta:
        model = Region
        base_type = RegionWithProject
        filterset_class = PublicProjectByRegionGqlFileterSet


class ExploreDeepProjectFilter(graphene.InputObjectType):
    created_at = graphene.Date()
    is_test_project = graphene.Boolean()
    search = graphene.String()
    organization = graphene.ID()
    is_entry_less_than = graphene.Boolean()


class ExploreDeepFilter(graphene.InputObjectType):
    date_from = graphene.Date(required=True)
    date_to = graphene.Date(required=True)
    project = ExploreDeepProjectFilter()


class Query:
    project = DjangoObjectField(ProjectDetailType)
    projects = DjangoPaginatedListObjectField(
        ProjectListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    recent_projects = graphene.List(graphene.NonNull(ProjectDetailType))
    recent_activities = graphene.List(graphene.NonNull(RecentActivityType))
    project_explore_stats = graphene.Field(ProjectExploreStatType)

    # only the region for which project are public
    projects_by_region = DjangoPaginatedListObjectField(ProjectByRegionListType)

    # PUBLIC NODES
    public_projects = DjangoPaginatedListObjectField(
        PublicProjectListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    public_projects_by_region = DjangoPaginatedListObjectField(
        PublicProjectByRegionListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    # Explore Deep Dashboard
    deep_explore_stats = graphene.Field(
        ExploreDashboardStatType,
        filter=ExploreDeepFilter(required=True)
    )

    # NOTE: This is a custom feature, see https://github.com/the-deep/graphene-django-extras
    # see: https://github.com/eamigo86/graphene-django-extras/compare/graphene-v2...the-deep:graphene-v2

    @staticmethod
    def resolve_recent_activities(root, info, **kwargs) -> QuerySet:
        return Project.get_recent_activities(info.context.user)

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
        return Region.objects\
            .filter(centroid__isnull=False)\
            .order_by('centroid')

    @staticmethod
    def resolve_project_explore_stats(root, info, **kwargs):
        return info.context.dl.project.resolve_explore_stats()

    # PUBLIC RESOLVERS
    @staticmethod
    def resolve_public_projects(root, info, **kwargs) -> QuerySet:
        return PublicProjectListType.queryset()

    @staticmethod
    def resolve_public_projects_by_region(*args, **kwargs):
        return Query.resolve_projects_by_region(*args, **kwargs)

    @staticmethod
    def resolve_deep_explore_stats(self, info, filter):
        if filter:
            date_from = filter.get('date_from')
            date_to = filter.get('date_to')

            # project specific filter
            project_qs = Project.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            project_filter = filter.get('project')
            if project_filter:
                search = project_filter.get('search')
                if search:
                    project_qs = project_qs.filter(
                        title__icontains=search,
                    )
                is_test_project = project_filter.get('is_test_project')
                if is_test_project:
                    project_qs = project_qs.filter(
                        is_test=True,
                    )
                is_entry_less_than = project_filter.get('is_entry_less_than')
                if is_entry_less_than:
                    project_qs = project_qs.filter(
                        entry__isnull=False
                    ).values('entry').annotate(
                        entry_count=models.Count('entry')
                    ).filter(entry_count__lte=100)

            total_projects = project_qs.count()
            total_registered_users = User.objects.filter(
                is_active=True,
            ).count()

            lead_qs = Lead.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            total_leads = lead_qs.distinct().count()

            entry_qs = Entry.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            total_entries = entry_qs.distinct().count()
            total_authors = lead_qs.values('authors').distinct().count()
            total_publishers = lead_qs.values('source').distinct().count()
            total_active_users = lead_qs.values('created_by').union(
                entry_qs.values('created_by')).count()

            organization_qs = Organization.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to
            )
            top_ten_authors = organization_qs.annotate(
                source_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        authors=models.OuterRef('pk')
                    ).order_by().values('authors')
                    .annotate(cnt=models.Count('*')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                project_count=models.functions.Coalesce(models.Subquery(
                    ProjectOrganization.objects.filter(
                        organization=models.OuterRef('pk')
                    ).order_by().values('organization')
                    .annotate(cnt=models.Count('project_id')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-project_count')[:10]

            top_ten_sources = organization_qs.annotate(
                source_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        source=models.OuterRef('pk')
                    ).order_by().values('source')
                    .annotate(cnt=models.Count('*')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                project_count=models.functions.Coalesce(models.Subquery(
                    ProjectOrganization.objects.filter(
                        organization=models.OuterRef('pk')
                    ).order_by().values('organization')
                    .annotate(cnt=models.Count('project_id')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-project_count')[:10]

            analysis_framework_qs = AnalysisFramework.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            top_ten_frameworks = analysis_framework_qs.annotate(
                project_count=models.functions.Coalesce(
                    models.Subquery(
                        Project.objects.filter(
                            analysis_framework=models.OuterRef('pk')
                        ).order_by().values('analysis_framework').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entry_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project__analysis_framework=models.OuterRef('pk')
                        ).order_by().values('project__analysis_framework').annotate(
                            count=models.Count('id', distinct=True)
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-project_count', '-entry_count').values(
                analysis_framework_id=models.F('id'),
                analysis_framework_title=models.F('title'),
                project_count=models.F('project_count'),
                entry_count=models.F('entry_count'),
            )[:10]

            top_ten_project_users = project_qs.annotate(
                user_count=models.functions.Coalesce(
                    models.Subquery(
                        ProjectMembership.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('member', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-user_count').values(
                project_id=models.F('id'),
                project_title=models.F('title'),
                user_count=models.F('user_count'),
            )

            top_ten_project_entries = project_qs.annotate(
                source_count=models.functions.Coalesce(
                    models.Subquery(
                        Lead.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entry_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-source_count', '-entry_count').values(
                project_id=models.F('id'),
                project_title=models.F('title'),
                source_count=models.F('source_count'),
                entry_count=models.F('entry_count')
            )[:10]

            return dict(
                total_projects=total_projects,
                total_registered_users=total_registered_users,
                total_leads=total_leads,
                total_entries=total_entries,
                total_authors=total_authors,
                total_publishers=total_publishers,
                total_active_users=total_active_users,
                top_ten_authors=top_ten_authors,
                top_ten_sources=top_ten_sources,
                top_ten_frameworks=top_ten_frameworks,
                top_ten_project_users=top_ten_project_users,
                top_ten_project_entries=top_ten_project_entries,
            )
