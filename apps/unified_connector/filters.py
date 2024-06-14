import django_filters
from django.db import models

from deep.filter_set import OrderEnumMixin
from utils.graphene.filters import (
    DateGteFilter,
    DateLteFilter,
    IDListFilter,
    MultipleInputFilter,
)

from .enums import (
    ConnectorLeadExtractionStatusEnum,
    ConnectorSourceLeadOrderingEnum,
    ConnectorSourceOrderingEnum,
    ConnectorSourceSourceEnum,
    ConnectorSourceStatusEnum,
    UnifiedConnectorOrderingEnum,
)
from .models import ConnectorSource, ConnectorSourceLead, UnifiedConnector


# ------------------------------ Graphql filters -----------------------------------
class UnifiedConnectorGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    ordering = MultipleInputFilter(UnifiedConnectorOrderingEnum, method="ordering_filter")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = UnifiedConnector
        fields = ()


class ConnectorSourceGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    ordering = MultipleInputFilter(ConnectorSourceOrderingEnum, method="ordering_filter")
    sources = MultipleInputFilter(ConnectorSourceSourceEnum, field_name="source")
    statuses = MultipleInputFilter(ConnectorSourceStatusEnum, field_name="status")
    unified_connectors = IDListFilter(field_name="unified_connector")

    class Meta:
        model = ConnectorSource
        fields = ()


class ConnectorSourceLeadGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(ConnectorSourceLeadOrderingEnum, method="ordering_filter")
    sources = IDListFilter(field_name="source")
    blocked = django_filters.BooleanFilter()
    already_added = django_filters.BooleanFilter()
    extraction_status = MultipleInputFilter(ConnectorLeadExtractionStatusEnum, field_name="connector_lead__extraction_status")

    search = django_filters.CharFilter(method="search_filter")
    author_organizations = IDListFilter(field_name="connector_lead__authors")
    published_on = django_filters.DateFilter(field_name="connector_lead__published_on")
    published_on_gte = DateGteFilter(field_name="connector_lead__published_on")
    published_on_lte = DateLteFilter(field_name="connector_lead__published_on")

    class Meta:
        model = ConnectorSourceLead
        fields = ()

    def search_filter(self, qs, _, value):
        # NOTE: This exists to make it compatible with post filter
        if not value:
            return qs
        return qs.filter(
            # By title
            models.Q(connector_lead__title__icontains=value)
            |
            # By source
            models.Q(connector_lead__source_raw__icontains=value)
            | models.Q(connector_lead__source__title__icontains=value)
            | models.Q(connector_lead__source__parent__title__icontains=value)
            |
            # By author
            models.Q(connector_lead__author_raw__icontains=value)
            | models.Q(connector_lead__authors__title__icontains=value)
            | models.Q(connector_lead__authors__parent__title__icontains=value)
            |
            # By URL
            models.Q(connector_lead__url__icontains=value)
            | models.Q(connector_lead__website__icontains=value)
        ).distinct()
