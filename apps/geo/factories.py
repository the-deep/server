import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from geo.models import Region


class RegionFactory(DjangoModelFactory):
    code = fuzzy.FuzzyText(length=3)
    title = factory.Sequence(lambda n: f'Region-{n}')

    class Meta:
        model = Region
