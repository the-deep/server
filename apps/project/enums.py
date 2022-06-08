import graphene
from django.db.models.functions import Lower

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)
from deep.permissions import ProjectPermissions as PP

from .models import (
    Project,
    ProjectRole,
    ProjectJoinRequest,
    ProjectOrganization,
    ProjectStats,
    ProjectMembership,
    ProjectUserGroupMembership,
)

ProjectPermissionEnum = graphene.Enum.from_enum(PP.Permission)
ProjectStatusEnum = convert_enum_to_graphene_enum(Project.Status, name='ProjectStatusEnum')
ProjectRoleTypeEnum = convert_enum_to_graphene_enum(ProjectRole.Type, name='ProjectRoleTypeEnum')
ProjectOrganizationTypeEnum = convert_enum_to_graphene_enum(ProjectOrganization.Type, name='ProjectOrganizationTypeEnum')
ProjectJoinRequestStatusEnum = convert_enum_to_graphene_enum(ProjectJoinRequest.Status, name='ProjectJoinRequestStatusEnum')
ProjectStatsStatusEnum = convert_enum_to_graphene_enum(ProjectStats.Status, name='ProjectStatsStatusEnum')
ProjectStatsActionEnum = convert_enum_to_graphene_enum(ProjectStats.Action, name='ProjectStatsActionEnum')
ProjectMembershipBadgeTypeEnum = convert_enum_to_graphene_enum(
    ProjectMembership.BadgeType, name='ProjectMembershipBadgeTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Project.status, ProjectStatusEnum),
        (ProjectOrganization.organization_type, ProjectOrganizationTypeEnum),
        (ProjectJoinRequest.status, ProjectJoinRequestStatusEnum),
        (ProjectStats.status, ProjectStatsStatusEnum),
        (ProjectMembership.badges, ProjectMembershipBadgeTypeEnum),
        (ProjectUserGroupMembership.badges, ProjectMembershipBadgeTypeEnum),
        (ProjectRole.type, ProjectRoleTypeEnum),
    )
}

# Additional enums which doesn't have a field in model but are used in serializer
enum_map.update({
    get_enum_name_from_django_field(
        None,
        field_name='action',  # ProjectVizConfigurationSerializer.action
        model_name=ProjectStats.__name__,
    ): ProjectStatsActionEnum,
})


class ProjectOrderingEnum(graphene.Enum):
    # ASC
    ASC_TITLE = Lower('title').asc()
    ASC_USER_COUNT = 'stats_cache__number_of_users'
    ASC_LEAD_COUNT = 'stats_cache__number_of_leads'
    ASC_CREATED_AT = 'created_at'
    ASC_ANALYSIS_FRAMEWORK = Lower('analysis_framework__title').asc()
    # DESC
    DESC_TITLE = Lower('title').desc()
    DESC_USER_COUNT = f'-{ASC_USER_COUNT}'
    DESC_LEAD_COUNT = f'-{ASC_LEAD_COUNT}'
    DESC_CREATED_AT = f'-{ASC_CREATED_AT}'
    DESC_ANALYSIS_FRAMEWORK = Lower('analysis_framework__title').desc()


class PublicProjectOrderingEnum(graphene.Enum):
    # ASC
    ASC_TITLE = Lower('title').asc()
    ASC_USER_COUNT = 'number_of_users'
    ASC_LEAD_COUNT = 'number_of_leads'
    ASC_CREATED_AT = 'created_at'
    ASC_ANALYSIS_FRAMEWORK = Lower('analysis_framework__title').asc()
    # DESC
    DESC_TITLE = Lower('title').desc()
    DESC_USER_COUNT = f'-{ASC_USER_COUNT}'
    DESC_LEAD_COUNT = f'-{ASC_LEAD_COUNT}'
    DESC_CREATED_AT = f'-{ASC_CREATED_AT}'
    DESC_ANALYSIS_FRAMEWORK = Lower('analysis_framework__title').desc()
