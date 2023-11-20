import django_filters

from deep.filter_set import generate_type_for_filter_set
from .models import DraftEntry
from utils.graphene.filters import IDListFilter, MultipleInputFilter
from .enums import (
    DraftEntryTypeEnum
)


class DraftEntryFilterSet(django_filters.FilterSet):
    lead = IDListFilter()
    draft_entry_type = MultipleInputFilter(DraftEntryTypeEnum)

    class Meta:
        model = DraftEntry
        fields = ()

    def filter_lead(self, qs, _, value):
        return qs if value is None else qs.filter(lead=value)

    def filter_draft_entry_type(self, qs, _, value):
        return qs if value is None else qs.filter(draft_entry_type=value)


DraftEntryFilterDataType, DraftEntryFilterDataInputType = generate_type_for_filter_set(
    DraftEntryFilterSet,
    "project.schema.ProjectListType",
    "DraftEntryFilterDataType",
    "DraftEntryFilterDataInputType",
)
