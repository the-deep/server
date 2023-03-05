import django_filters

from utils.graphene.filters import IDListFilter
from user_resource.filters import UserResourceGqlFilterSet
from entry.filter_set import EntryGQFilterSet

from .models import (
    Analysis,
    AnalysisPillar,
    DiscardedEntry,
    AnalyticalStatement,
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
        choices=DiscardedEntry.TagType.choices,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = DiscardedEntry
        fields = []


# -------------------- Graphql Filters -----------------------------------
class AnalysisGQFilterSet(UserResourceGqlFilterSet):
    class Meta:
        model = Analysis
        fields = ()


class AnalysisPillarGQFilterSet(UserResourceGqlFilterSet):
    analyses = IDListFilter(field_name='analysis')

    class Meta:
        model = AnalysisPillar
        fields = ()


class AnalysisPillarEntryGQFilterSet(EntryGQFilterSet):
    discarded = django_filters.BooleanFilter(method='filter_discarded')
    exclude_entries = IDListFilter(method='filter_exclude_entries')

    def filter_discarded(self, queryset, _, value):
        # NOTE: This is only for argument, filter is done in AnalysisPillarType.resolve_entries
        return queryset

    def filter_exclude_entries(self, queryset, _, value):
        if value:
            return queryset.exclude(id__in=value)
        return queryset


class AnalyticalStatementGQFilterSet(UserResourceGqlFilterSet):
    class Meta:
        model = AnalyticalStatement
        fields = ()
