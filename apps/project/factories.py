import factory
from factory.django import DjangoModelFactory

from .models import Project, ProjectJoinRequest


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f'Project-{n}')


class ProjectJoinRequestFactory(DjangoModelFactory):
    class Meta:
        model = ProjectJoinRequest
