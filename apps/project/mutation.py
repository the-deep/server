from django.utils.translation import gettext

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from django.core.exceptions import PermissionDenied

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType

from deep.permissions import ProjectPermissions as PP

from lead.mutation import Mutation as LeadMutation
from entry.mutation import Mutation as EntryMutation

from .models import Project, ProjectJoinRequest
from .serializers import ProjectJoinGqSerializer, ProjectAcceptRejectSerializer
from .schema import ProjectJoinRequestType


ProjectJoinRequestInputType = generate_input_type_for_serializer(
    'ProjectJoinRequestInputType',
    serializer_class=ProjectJoinGqSerializer,
)

ProjectAcceptRejectInputType = generate_input_type_for_serializer(
    'ProjectAcceptRejectInputType',
    serializer_class=ProjectAcceptRejectSerializer,
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


class ProjectMutationType(
    LeadMutation,
    EntryMutation,
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
