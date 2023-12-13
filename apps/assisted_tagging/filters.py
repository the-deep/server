import django_filters

from deep.filter_set import generate_type_for_filter_set
from .models import DraftEntry
from utils.graphene.filters import IDListFilter, MultipleInputFilter
from .enums import (
    DraftEntryTypeEnum
)


class DraftEntryFilterSet(django_filters.FilterSet):
    leads = IDListFilter(field_name='lead')
    draft_entry_types = MultipleInputFilter(DraftEntryTypeEnum, field_name='draft_entry_type')
    is_discarded = django_filters.BooleanFilter(method='filter_discarded')

    def filter_discarded(self, queryset, name, value):
        if value:
            return queryset.filter(is_discarded=value)
        return queryset.filter(is_discarded = False)

    class Meta:
        model = DraftEntry
        fields = ()


DraftEntryFilterDataType, DraftEntryFilterDataInputType = generate_type_for_filter_set(
    DraftEntryFilterSet,
    "project.schema.ProjectListType",
    "DraftEntryFilterDataType",
    "DraftEntryFilterDataInputType",
)
