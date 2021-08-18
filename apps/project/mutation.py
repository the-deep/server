from django.utils.translation import gettext

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from django.core.exceptions import PermissionDenied

from utils.graphene.mutation import generate_input_type_for_serializer
from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType

from lead.mutation import Mutation as LeadMutation
from entry.mutation import Mutation as EntryMutation

from .models import Project, ProjectJoinRequest
from .serializers import ProjectJoinGqSerializer, ProjectJoinCancelGqSerializer
from .schema import ProjectJoinRequestType


ProjectJoinRequestInputType = generate_input_type_for_serializer(
    'ProjectJoinRequestInputType',
    serializer_class=ProjectJoinGqSerializer,
)

ProjectJoinCancelInputType = generate_input_type_for_serializer(
    'ProjectJoinCancelInputType',
    serializer_class=ProjectJoinCancelGqSerializer,
)


class DeleteProjectJoin(graphene.Mutation):
    class Arguments:
        data = ProjectJoinCancelInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ProjectJoinRequestType)

    @staticmethod
    def mutate(root, info, data):
        try:
            instance = ProjectJoinRequest.objects.get(requested_by=info.context.user,
                                                      status=ProjectJoinRequest.Status.PENDING,
                                                      project=data['project'])
        except ProjectJoinRequest.DoesNotExist:
            return DeleteProjectJoin(errors=[
                dict(field='nonFieldErrors', messages=gettext('ProjectJoinRequest does not exist.'))
            ], ok=False)
        instance.delete()
        return DeleteProjectJoin(result=instance, errors=None, ok=True)


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
    cancel_project_join = DeleteProjectJoin.Field()
    project = DjangoObjectField(ProjectMutationType)
    # TODO: For project mutation make sure AF permission is checked when using. (Public and Private logics)
