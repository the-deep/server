import factory
from factory.django import DjangoModelFactory

from unified_connector.models import (
    UnifiedConnector,
    ConnectorSource,
    ConnectorLead,
    ConnectorSourceLead,
)


class UnifiedConnectorFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Unified-Connector-{n}')

    class Meta:
        model = UnifiedConnector


class ConnectorSourceFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Connector-Source-{n}')

    class Meta:
        model = ConnectorSource


class ConnectorLeadFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Connector-Lead-{n}')
    url = factory.Sequence(lambda n: f'https://example.com/path-{n}')

    class Meta:
        model = ConnectorLead

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for author in extracted:
                self.authors.add(author)


class ConnectorSourceLeadFactory(DjangoModelFactory):
    class Meta:
        model = ConnectorSourceLead
