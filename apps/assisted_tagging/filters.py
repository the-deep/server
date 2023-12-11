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

    class Meta:
        model = DraftEntry
        fields = ()


DraftEntryFilterDataType, DraftEntryFilterDataInputType = generate_type_for_filter_set(
    DraftEntryFilterSet,
    "project.schema.ProjectListType",
    "DraftEntryFilterDataType",
    "DraftEntryFilterDataInputType",
)
