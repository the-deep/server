import django_filters

from .models import DraftEntry
from utils.graphene.filters import IDFilter, MultipleInputFilter
from .enums import (
    DraftEntryTypeEnum
)


class DraftEntryFilterSet(django_filters.FilterSet):
    lead = IDFilter(field_name='lead')
    draft_entry_types = MultipleInputFilter(DraftEntryTypeEnum, field_name='type')
    is_discarded = django_filters.BooleanFilter()

    class Meta:
        model = DraftEntry
        fields = ()
