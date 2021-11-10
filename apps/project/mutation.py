from django.utils.translation import gettext

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from django.core.exceptions import PermissionDenied

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsBulkGrapheneMutation,
)
from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType

from deep.permissions import ProjectPermissions as PP

from lead.mutation import Mutation as LeadMutation
from entry.mutation import Mutation as EntryMutation
from quality_assurance.mutation import Mutation as QualityAssuranceMutation
from ary.mutation import Mutation as AryMutation

from .models import (
    Project,
    ProjectStats,
    ProjectJoinRequest,
    ProjectMembership,
    ProjectUserGroupMembership,
)
from .serializers import (
    ProjectJoinGqSerializer,
    ProjectAcceptRejectSerializer,
    ProjectMembershipGqlSerializer as ProjectMembershipSerializer,
    ProjectUserGroupMembershipGqlSerializer as ProjectUserGroupMembershipSerializer,
    ProjectVizConfigurationSerializer,
)
from .schema import (
    ProjectJoinRequestType,
    ProjectMembershipType,
    ProjectUserGroupMembershipType,
    ProjectVizDataType,
)


ProjectJoinRequestInputType = generate_input_type_for_serializer(
    'ProjectJoinRequestInputType',
    serializer_class=ProjectJoinGqSerializer,
)

ProjectAcceptRejectInputType = generate_input_type_for_serializer(
    'ProjectAcceptRejectInputType',
    serializer_class=ProjectAcceptRejectSerializer,
)

ProjectMembershipInputType = generate_input_type_for_serializer(
    'ProjectMembershipInputType',
    serializer_class=ProjectMembershipSerializer,
)

ProjectUserGroupMembershipInputType = generate_input_type_for_serializer(
    'ProjectUserGroupMembershipInputType',
    serializer_class=ProjectUserGroupMembershipSerializer,
)

ProjectVizConfigurationInputType = generate_input_type_for_serializer(
    'ProjectVizConfigurationInputType',
    serializer_class=ProjectVizConfigurationSerializer,
)


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
            instance = ProjectJoinRequest.objects.get(requested_by=info.context.user,
                                                      status=ProjectJoinRequest.Status.PENDING,
                                                      project=project_id)
        except ProjectJoinRequest.DoesNotExist:
            return ProjectJoinRequestDelete(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext('ProjectJoinRequest does not exist for project(id:%s)' % project_id)
                )
            ], ok=False)
        instance.delete()
        instance.id = id
        return ProjectJoinRequestDelete(result=instance, errors=None, ok=True)


class CreateProjectJoin(graphene.Mutation):
    class Arguments:
        data = ProjectJoinRequestInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ProjectJoinRequestType)

    @staticmethod
    def mutate(root, info, data):
        serializer = ProjectJoinGqSerializer(data=data, context={'request': info.context.request})
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
                member__in=[info.context.user, project.created_by]
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


class UpdateProjectVizConfiguration(PsGrapheneMutation):
    class Arguments:
        data = ProjectVizConfigurationInputType(required=True)

    result = graphene.Field(ProjectVizDataType)
    model = ProjectStats
    serializer_class = ProjectVizConfigurationSerializer
    permissions = [PP.Permission.UPDATE_PROJECT]


class ProjectMutationType(
    # --Begin Project Scoped Mutation
    LeadMutation,
    EntryMutation,
    QualityAssuranceMutation,
    AryMutation,
    # --End Project Scoped Mutation
    DjangoObjectType
):
    """
    This mutation is for other scoped objects
    """
    class Meta:
        model = Project
        skip_registry = True
        fields = ('id', 'title')

    accept_reject_project = ProjectAcceptReject.Field()
    project_user_membership_bulk = BulkUpdateProjectMembership.Field()
    project_user_group_membership_bulk = BulkUpdateProjectUserGroupMembership.Field()
    project_viz_configuration_update = UpdateProjectVizConfiguration.Field()

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            project = Project.get_for_gq(info.context.user, only_member=True).get(pk=id)
            info.context.set_active_project(project)
            return project
        except Project.DoesNotExist:
            raise PermissionDenied()


class Mutation(object):
    join_project = CreateProjectJoin.Field()
    project_join_request_delete = ProjectJoinRequestDelete.Field()
    project = DjangoObjectField(ProjectMutationType)
    # TODO: For project mutation make sure AF permission is checked when using. (Public and Private logics)
