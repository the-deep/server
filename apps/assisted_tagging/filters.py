import django_filters

from .models import DraftEntry
from utils.graphene.filters import (
    IDFilter,
    MultipleInputFilter,
    IDListFilter,
)
from .enums import (
    DraftEntryTypeEnum
)


class DraftEntryFilterSet(django_filters.FilterSet):
    lead = IDFilter(field_name='lead')
    draft_entry_types = MultipleInputFilter(DraftEntryTypeEnum, field_name='type')
    ignore_ids = IDListFilter(method='filter_ignore_draft_ids', help_text='Ids are filtered out.')
    is_discarded = django_filters.BooleanFilter()

    class Meta:
        model = DraftEntry
        fields = ()

    def filter_ignore_draft_ids(self, qs, _, value):
        if value is None:
            return qs
        return qs.exclude(id__in=value)
