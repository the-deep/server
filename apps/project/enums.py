from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import (
    Project,
    ProjectJoinRequest,
    ProjectOrganization,
    ProjectStats,
)

ProjectStatusEnum = convert_enum_to_graphene_enum(Project.Status, name='ProjectStatusEnum')
ProjectOrganizationTypeEnum = convert_enum_to_graphene_enum(ProjectOrganization.Type, name='ProjectOrganizationTypeEnum')
ProjectJoinRequestStatusEnum = convert_enum_to_graphene_enum(ProjectJoinRequest.Status, name='ProjectJoinRequestStatusEnum')
ProjectStatsStatusEnum = convert_enum_to_graphene_enum(ProjectStats.Status, name='ProjectStatsStatusEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Project.status, ProjectStatusEnum),
        (ProjectOrganization.organization_type, ProjectOrganizationTypeEnum),
        (ProjectJoinRequest.status, ProjectJoinRequestStatusEnum),
        (ProjectStats.status, ProjectStatsStatusEnum),
    )
}
