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


class ConnectorSourceLeadFactory(DjangoModelFactory):
    class Meta:
        model = ConnectorSourceLead
