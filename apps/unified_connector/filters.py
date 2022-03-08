import django_filters


from deep.filter_set import OrderEnumMixin
from utils.graphene.filters import (
    MultipleInputFilter,
    IDListFilter,
)

from .models import (
    ConnectorSource,
    ConnectorSourceLead,
    UnifiedConnector,
)
from .enums import (
    ConnectorSourceSourceEnum,
    ConnectorLeadExtractionStatusEnum,
    ConnectorSourceLeadOrderingEnum,
    ConnectorSourceOrderingEnum,
    ConnectorSourceStatusEnum,
    UnifiedConnectorOrderingEnum,
)


# ------------------------------ Graphql filters -----------------------------------
class UnifiedConnectorGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    search = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    ordering = MultipleInputFilter(UnifiedConnectorOrderingEnum, method='ordering_filter')
    is_active = django_filters.BooleanFilter()

    class Meat:
        model = UnifiedConnector
        fields = ()


class ConnectorSourceGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    search = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    ordering = MultipleInputFilter(ConnectorSourceOrderingEnum, method='ordering_filter')
    sources = MultipleInputFilter(ConnectorSourceSourceEnum, field_name='source')
    statuses = MultipleInputFilter(ConnectorSourceStatusEnum, field_name='status')
    unified_connectors = IDListFilter(field_name='unified_connector')

    class Meat:
        model = ConnectorSource
        fields = ()


class ConnectorSourceLeadGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(ConnectorSourceLeadOrderingEnum, method='ordering_filter')
    sources = IDListFilter(field_name='source')
    blocked = django_filters.BooleanFilter()
    already_added = django_filters.BooleanFilter()
    extraction_status = MultipleInputFilter(
        ConnectorLeadExtractionStatusEnum, field_name='connector_lead__extraction_status')

    class Meat:
        model = ConnectorSourceLead
        fields = ()
