from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from lead.mutation import CreateLead
from project.schema import ProjectTypeMixin
from .models import Project


class ProjectMutation(ProjectTypeMixin, DjangoObjectType):
    create_lead = CreateLead.Field()

    class Meta:
        model = Project
        skip_registry = True
        fields = ('id', 'title')


class Mutation():
    project = DjangoObjectField(ProjectMutation)
