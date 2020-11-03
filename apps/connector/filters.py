from django_filters import rest_framework as filters

from .models import (
    ConnectorLead,

    UnifiedConnector,
    UnifiedConnectorSourceLead,
)


class UnifiedConnectorFilterSet(filters.FilterSet):
    class Meta:
        model = UnifiedConnector
        fields = ('is_active',)


class UnifiedConnectorSourceLeadFilterSet(filters.FilterSet):
    search = filters.CharFilter(label='Search', method='search_filter')
    status = filters.ChoiceFilter(
        label='Status', choices=ConnectorLead.Status.CHOICES, field_name='lead__status', distinct=True,
    )

    class Meta:
        model = UnifiedConnectorSourceLead
        fields = ('already_added', 'blocked',)

    def search_filter(self, qs, name, value):
        # NOTE: This exists to make it compatible with post filter
        return qs.filter(lead__data__title__icontains=value)
