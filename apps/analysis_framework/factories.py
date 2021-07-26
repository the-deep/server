import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import AnalysisFramework


class AnalysisFrameworkFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'AF-{n}')
    description = fuzzy.FuzzyText(length=100)

    class Meta:
        model = AnalysisFramework
