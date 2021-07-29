from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from django.core.exceptions import PermissionDenied

from lead.mutation import Mutation as LeadMutation
from .models import Project


class ProjectMutationType(
    LeadMutation,
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


class Mutation():
    project = DjangoObjectField(ProjectMutationType)
    # TODO: For project mutation make sure AF permission is checked when using.
