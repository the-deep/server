import django_filters


from deep.filter_set import OrderEnumMixin
from utils.graphene.filters import MultipleInputFilter

from .models import (
    ConnectorSource,
    ConnectorSourceLead,
    UnifiedConnector,
)
from .enums import (
    ConnectorSourceLeadOrderingEnum,
    ConnectorSourceOrderingEnum,
    UnifiedConnectorOrderingEnum,
)


# ------------------------------ Graphql filters -----------------------------------
class UnifiedConnectorGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(UnifiedConnectorOrderingEnum, method='ordering_filter')

    class Meat:
        model = UnifiedConnector
        fields = ()


class ConnectorSourceGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(ConnectorSourceOrderingEnum, method='ordering_filter')

    class Meat:
        model = ConnectorSource
        fields = ()


class ConnectorSourceLeadGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(ConnectorSourceLeadOrderingEnum, method='ordering_filter')

    class Meat:
        model = ConnectorSourceLead
        fields = ()
