import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from geo.models import (
    Region,
    AdminLevel,
    GeoArea,
)


class RegionFactory(DjangoModelFactory):
    code = fuzzy.FuzzyText(length=3)
    title = factory.Sequence(lambda n: f'Region-{n}')

    class Meta:
        model = Region


class AdminLevelFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Region-{n}')

    class Meta:
        model = AdminLevel


class GeoAreaFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'GeoArea-{n}')
    code = factory.Sequence(lambda n: f'code-{n}')

    class Meta:
        model = GeoArea
