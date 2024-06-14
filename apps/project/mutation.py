import graphene
from analysis.mutation import Mutation as AnalysisMutation
from ary.mutation import Mutation as AryMutation
from assessment_registry.mutation import ProjectMutation as AssessmentRegistryMutation
from assisted_tagging.mutation import AssistedTaggingMutationType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils.translation import gettext
from entry.mutation import Mutation as EntryMutation
from export.mutation import ProjectMutation as ExportMutation
from geo.models import Region
from geo.schema import RegionDetailType
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from lead.mutation import Mutation as LeadMutation
from quality_assurance.mutation import Mutation as QualityAssuranceMutation
from unified_connector.mutation import UnifiedConnectorMutationType

from deep.permissions import ProjectPermissions as PP
from deep.trackers import TrackerAction, track_project
from utils.graphene.error_types import CustomErrorType, mutation_is_not_valid
from utils.graphene.mutation import (
    DeleteMutation,
    GrapheneMutation,
    PsBulkGrapheneMutation,
    PsGrapheneMutation,
    generate_input_type_for_serializer,
)

from .models import (
    Project,
    ProjectJoinRequest,
    ProjectMembership,
    ProjectPinned,
    ProjectRole,
    ProjectStats,
    ProjectUserGroupMembership,
)
from .schema import (
    ProjectDetailType,
    ProjectJoinRequestType,
    ProjectMembershipType,
    ProjectUserGroupMembershipType,
    ProjectVizDataType,
    UserPinnedProjectType,
)
from .serializers import (
    BulkProjectPinnedSerializer,
    ProjectAcceptRejectSerializer,
    ProjectGqSerializer,
    ProjectJoinGqSerializer,
)
from .serializers import ProjectMembershipGqlSerializer as ProjectMembershipSerializer
from .serializers import (
    ProjectUserGroupMembershipGqlSerializer as ProjectUserGroupMembershipSerializer,
)
from .serializers import ProjectVizConfigurationSerializer, UserPinnedProjectSerializer

ProjectCreateInputType = generate_input_type_for_serializer(
    "ProjectCreateInputType",
    serializer_class=ProjectGqSerializer,
)

ProjectUpdateInputType = generate_input_type_for_serializer(
    "ProjectUpdateInputType",
    serializer_class=ProjectGqSerializer,
    partial=True,
)

ProjectJoinRequestInputType = generate_input_type_for_serializer(
    "ProjectJoinRequestInputType",
    serializer_class=ProjectJoinGqSerializer,
)

ProjectAcceptRejectInputType = generate_input_type_for_serializer(
    "ProjectAcceptRejectInputType",
    serializer_class=ProjectAcceptRejectSerializer,
)

ProjectMembershipInputType = generate_input_type_for_serializer(
    "ProjectMembershipInputType",
    serializer_class=ProjectMembershipSerializer,
)

ProjectUserGroupMembershipInputType = generate_input_type_for_serializer(
    "ProjectUserGroupMembershipInputType",
    serializer_class=ProjectUserGroupMembershipSerializer,
)

ProjectVizConfigurationInputType = generate_input_type_for_serializer(
    "ProjectVizConfigurationInputType",
    serializer_class=ProjectVizConfigurationSerializer,
)

ProjectPinnedInputType = generate_input_type_for_serializer(
    "ProjectPinnedInputType", serializer_class=UserPinnedProjectSerializer
)

UserPinnedProjectReOrderInputType = generate_input_type_for_serializer(
    "UserPinnedProjectReOrderInputType",
    serializer_class=BulkProjectPinnedSerializer,
)


class CreateProject(GrapheneMutation):
    class Arguments:
        data = ProjectCreateInputType(required=True)

    result = graphene.Field(ProjectDetailType)
    # class vars
    serializer_class = ProjectGqSerializer
    model = Project

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to create New Project


class UpdateProject(PsGrapheneMutation):
    class Arguments:
        data = ProjectUpdateInputType(required=True)

    result = graphene.Field(ProjectDetailType)
    # class vars
    serializer_class = ProjectGqSerializer
    model = Project
    permissions = [PP.Permission.UPDATE_PROJECT]

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        kwargs["id"] = info.context.active_project.id
        return super().perform_mutate(root, info, **kwargs)


class ProjectAcceptReject(PsGrapheneMutation):
    class Arguments:
        data = ProjectAcceptRejectInputType(required=True)
        id = graphene.ID(required=True)

    model = ProjectJoinRequest
    serializer_class = ProjectAcceptRejectSerializer
    result = graphene.Field(ProjectJoinRequestType)
    permissions = [PP.Permission.UPDATE_PROJECT]


class ProjectJoinRequestDelete(graphene.Mutation):
    class Arguments:
        project_id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ProjectJoinRequestType)

    @staticmethod
    def mutate(root, info, project_id):
        try:
            instance = ProjectJoinRequest.objects.get(
                requested_by=info.context.user,
                status=ProjectJoinRequest.Status.PENDING,
                project=project_id,
            )
        except ProjectJoinRequest.DoesNotExist:
            return ProjectJoinRequestDelete(
                errors=[
                    dict(
                        field="nonFieldErrors",
                        messages=gettext("ProjectJoinRequest does not exist for project(id:%s)" % project_id),
                    )
                ],
                ok=False,
            )
        instance.delete()
        instance.id = id
        return ProjectJoinRequestDelete(result=instance, errors=None, ok=True)


class ProjectDelete(DeleteMutation):
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(ProjectDetailType)

    @staticmethod
    def mutate(root, info, **kwargs):
        membership_qs = ProjectMembership.objects.filter(
            project=info.context.active_project.id,
            member=info.context.user,
            role__type=ProjectRole.Type.PROJECT_OWNER,
        )
        if not membership_qs.exists():
            return ProjectDelete(
                errors=[
                    dict(
                        field="nonFieldErrors",
                        messages=gettext(
                            "You should be Project Owner to delete this project(id:%s)" % info.context.active_project.id
                        ),
                    )
                ],
                ok=False,
            )
        root.soft_delete()
        return ProjectDelete(result=root, errors=None, ok=True)


class CreateProjectJoin(graphene.Mutation):
    class Arguments:
        data = ProjectJoinRequestInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ProjectJoinRequestType)

    @staticmethod
    def mutate(root, info, data):
        serializer = ProjectJoinGqSerializer(data=data, context={"request": info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateProjectJoin(errors=errors, ok=False)
        instance = serializer.save()
        return CreateProjectJoin(result=instance, errors=None, ok=True)


class BulkProjectMembershipInputType(ProjectMembershipInputType):
    id = graphene.ID()


class BulkProjectUserGroupMembershipInputType(ProjectUserGroupMembershipInputType):
    id = graphene.ID()


class BulkUpdateProjectMembership(PsBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkProjectMembershipInputType))
        delete_ids = graphene.List(graphene.NonNull(graphene.ID))

    result = graphene.List(ProjectMembershipType)
    deleted_result = graphene.List(graphene.NonNull(ProjectMembershipType))
    # class vars
    serializer_class = ProjectMembershipSerializer
    model = ProjectMembership
    permissions = [PP.Permission.CAN_ADD_MEMBER]

    @classmethod
    def get_valid_delete_items(cls, info, delete_ids):
        project = info.context.active_project
        user_membership = ProjectMembership.objects.filter(
            project=project,
            member=info.context.user,
        ).first()
        if user_membership:
            return ProjectMembership.objects.filter(
                pk__in=delete_ids,  # id's provided
                project=project,  # For active Project
                role__level__gt=user_membership.role.level,  # Only allow for lower level roles.
            ).exclude(
                # Exclude yourself and owner of the Project
                member__in=[info.context.user, project.created_by],
                # Also exclude memberships from usergroups
                linked_group__isnull=False,
            )
        return ProjectMembership.objects.none()


class BulkUpdateProjectUserGroupMembership(PsBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkProjectUserGroupMembershipInputType))
        delete_ids = graphene.List(graphene.NonNull(graphene.ID))

    result = graphene.List(ProjectUserGroupMembershipType)
    deleted_result = graphene.List(graphene.NonNull(ProjectUserGroupMembershipType))
    # class vars
    serializer_class = ProjectUserGroupMembershipSerializer
    model = ProjectUserGroupMembership
    permissions = [PP.Permission.CAN_ADD_MEMBER]

    @classmethod
    def get_valid_delete_items(cls, info, delete_ids):
        project = info.context.active_project
        user_membership = ProjectMembership.objects.filter(
            project=project,
            member=info.context.user,
        ).first()
        if user_membership:
            return ProjectUserGroupMembership.objects.filter(
                pk__in=delete_ids,  # id's provided
                project=project,  # For active Project
                role__level__gt=user_membership.role.level,  # Only allow for lower level roles.
            )
        return ProjectUserGroupMembership.objects.none()


class BulkUpdateProjectRegion(PsBulkGrapheneMutation):
    class Arguments:
        regions_to_add = graphene.List(graphene.NonNull(graphene.ID))
        regions_to_remove = graphene.List(graphene.NonNull(graphene.ID))

    result = graphene.List(graphene.NonNull(RegionDetailType))
    deleted_result = graphene.List(graphene.NonNull(RegionDetailType))
    # class vars
    model = Project.regions.through
    permissions = [PP.Permission.UPDATE_PROJECT]

    @classmethod
    def perform_mutate(cls, _, info, **kwargs):
        project = info.context.active_project
        regions_to_add = kwargs.get("regions_to_add") or []
        regions_to_remove = kwargs.get("regions_to_remove") or []
        existing_regions = project.regions.all()
        added_regions = [
            region
            for region in Region.objects.filter(id__in=regions_to_add)
            .exclude(id__in=existing_regions.values("id"))
            .order_by("id")
            if region.public or region.can_modify(info.context.user)
        ]
        deleted_regions = list(existing_regions.filter(id__in=regions_to_remove).order_by("id"))
        assert len(added_regions) <= len(regions_to_add)
        assert len(deleted_regions) <= len(regions_to_remove)
        # Remove regions
        project.regions.remove(*deleted_regions)
        # Add regions
        project.regions.add(*added_regions)
        return cls(result=added_regions, deleted_result=deleted_regions)


class UpdateProjectVizConfiguration(PsGrapheneMutation):
    class Arguments:
        data = ProjectVizConfigurationInputType(required=True)

    result = graphene.Field(ProjectVizDataType)
    model = ProjectStats
    serializer_class = ProjectVizConfigurationSerializer
    permissions = [PP.Permission.UPDATE_PROJECT]


class CreateUserPinnedProject(PsGrapheneMutation):
    class Arguments:
        data = ProjectPinnedInputType(required=True)

    model = ProjectPinned
    result = graphene.Field(UserPinnedProjectType)
    serializer_class = UserPinnedProjectSerializer
    permissions = []


class ProjectMutationType(
    # --Begin Project Scoped Mutation
    LeadMutation,
    EntryMutation,
    QualityAssuranceMutation,
    AryMutation,
    ExportMutation,
    AnalysisMutation,
    AssessmentRegistryMutation,
    # --End Project Scoped Mutation
    DjangoObjectType,
):
    """
    This mutation is for other scoped objects
    """

    class Meta:
        model = Project
        skip_registry = True
        fields = ("id", "title")

    project_update = UpdateProject.Field()
    project_delete = ProjectDelete.Field()
    accept_reject_project = ProjectAcceptReject.Field()
    project_user_membership_bulk = BulkUpdateProjectMembership.Field()
    project_user_group_membership_bulk = BulkUpdateProjectUserGroupMembership.Field()
    project_region_bulk = BulkUpdateProjectRegion.Field()
    project_viz_configuration_update = UpdateProjectVizConfiguration.Field()
    unified_connector = graphene.Field(UnifiedConnectorMutationType)
    assisted_tagging = graphene.Field(AssistedTaggingMutationType)

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            project = Project.get_for_gq(info.context.user, only_member=True).get(pk=id)
            info.context.set_active_project(project)
            track_project(project, action=TrackerAction.Project.WRITE)
            return project
        except Project.DoesNotExist:
            raise PermissionDenied()

    @staticmethod
    def resolve_unified_connector(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return {}

    @staticmethod
    def resolve_assisted_tagging(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return {}


class ReorderPinnedProjects(PsGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(UserPinnedProjectReOrderInputType))

    model = ProjectPinned
    result = graphene.List(UserPinnedProjectType)
    serializer_class = BulkProjectPinnedSerializer
    permissions = []

    @classmethod
    @transaction.atomic()
    def perform_mutate(cls, root, info, **kwargs):
        errors_data = []
        serializers_data = []
        results = []
        for data in kwargs["items"]:
            instance, errors = cls.get_object(info, id=data["id"])
            if errors:
                errors_data.append(errors)
            serializer = cls.serializer_class(data=data, instance=instance, context={"request": info.context.request})
            errors_data.append(mutation_is_not_valid(serializer))  # errors_data also add empty list
            serializers_data.append(serializer)
        errors_data = [items for items in errors_data if items]  # list comprehension removing empty list
        if errors_data:
            return cls(errors=errors_data, ok=False)
        for serializer in serializers_data:
            results.append(serializer.save())
        return cls(result=results, ok=True)


class DeleteUserPinnedProject(DeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = ProjectPinned
    result = graphene.Field(UserPinnedProjectType)
    permissions = []

    @staticmethod
    def mutate(root, info, id):

        project_pinned_qs = ProjectPinned.objects.filter(id=id, user=info.context.user)
        if not project_pinned_qs.exists():
            return DeleteUserPinnedProject(
                errors=[
                    dict(
                        field="nonFieldErrors",
                        messages=gettext("Not authorize the unpinned project "),
                    )
                ],
                ok=False,
            )
        project_pinned_qs.delete()
        return DeleteUserPinnedProject(result=root, errors=None, ok=True)


class Mutation(object):
    project_create = CreateProject.Field()
    join_project = CreateProjectJoin.Field()
    project_join_request_delete = ProjectJoinRequestDelete.Field()
    project = DjangoObjectField(ProjectMutationType)
    create_user_pinned_project = CreateUserPinnedProject.Field()
    reorder_pinned_projects = ReorderPinnedProjects.Field()
    delete_user_pinned_project = DeleteUserPinnedProject.Field()
