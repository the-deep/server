import factory
from factory.django import DjangoModelFactory

from .models import Project, ProjectJoinRequest


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f'Project-{n}')

    @factory.post_generation
    def regions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for region in extracted:
                self.regions.add(region)


class ProjectJoinRequestFactory(DjangoModelFactory):
    class Meta:
        model = ProjectJoinRequest
