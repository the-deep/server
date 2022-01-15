import graphene

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


# TODO: Define this dynamically through a list?
class PublicProjectOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_CREATED_AT = 'created_at'
    ASC_TITLE = 'title'
    ASC_USERS_COUNT = 'number_of_users'
    ASC_SOURCES_COUNT = 'number_of_leads'
    # DESC
    DESC_ID = '-id'
    DESC_CREATED_AT = '-created_at'
    DESC_TITLE = '-title'
    DESC_USERS_COUNT = '-number_of_users'
    DESC_SOURCES_COUNT = '-number_of_leads'
