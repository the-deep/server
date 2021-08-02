import factory
from factory.django import DjangoModelFactory

from .models import Export


class ExportFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Export-{n}')
    status = factory.fuzzy.FuzzyChoice(Export.Status)
    type = factory.fuzzy.FuzzyChoice(Export.DataType)

    class Meta:
        model = Export
