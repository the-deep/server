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
    status = filters.ChoiceFilter(choices=ConnectorLead.Status.CHOICES, field_name='lead__status', distinct=True)

    class Meta:
        model = UnifiedConnectorSourceLead
        fields = ('already_added', 'blocked',)
