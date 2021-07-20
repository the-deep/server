import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from gallery.factories import FileFactory

from .models import Organization, OrganizationType


class OrganizationTypeFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Organization-Type-{n}')
    short_name = factory.Sequence(lambda n: f'Organization-Type-Short-Name-{n}')
    description = fuzzy.FuzzyText(length=100)

    class Meta:
        model = OrganizationType


class OrganizationFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Organization-{n}')
    organization_type = factory.SubFactory(OrganizationTypeFactory)
    short_name = factory.Sequence(lambda n: f'Organization-Short-Name-{n}')
    long_name = factory.Sequence(lambda n: f'Organization-Long-Name-{n}')
    url = fuzzy.FuzzyText(length=50, prefix='https://example.com/')
    logo = factory.SubFactory(FileFactory)
    verified = True

    class Meta:
        model = Organization
