import factory
from factory.django import DjangoModelFactory

from .models import Project


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f'Project-{n}')
