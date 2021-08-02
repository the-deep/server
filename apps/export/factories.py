import factory
from factory.django import DjangoModelFactory

from project.factories import ProjectFactory
from user.factories import UserFactory
from .models import Export


class ExportFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Export-{n}')
    exported_by = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    status = factory.fuzzy.FuzzyChoice(Export.Status)
    type = factory.fuzzy.FuzzyChoice(Export.DataType)

    class Meta:
        model = Export
