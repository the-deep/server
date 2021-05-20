import django_filters

from entry.filter_set import EntryFilterSet
from .models import (
    Analysis,
    DiscardedEntry
)


class AnalysisFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lt',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__gt = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gt',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lte',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at = django_filters.DateTimeFilter(
        field_name='created_at',
        input_formats=['%Y-%m-%d%z'],
    )

    class Meta:
        model = Analysis
        fields = ()


class DiscardedEntryFilterSet(django_filters.FilterSet):
    tag = django_filters.MultipleChoiceFilter(
        choices=DiscardedEntry.TagType.choices(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = DiscardedEntry
        fields = []
