from django.db.models import query
import django_filters
from django_enumfield.forms.fields import EnumChoiceField


from entry.filter_set import EntryFilterSet
from entry.models import Entry
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


class DisCardedEntryFilterSet(django_filters.FilterSet):
    tag = django_filters.MultipleChoiceFilter(
        choices=DiscardedEntry.TAG_TYPE.choices(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = DiscardedEntry
        fields = []


class AnalysisPillarEntryFilterSet(EntryFilterSet):
    TRUE = 'true'
    FALSE = 'false'
    BOOLEAN_CHOICES = (
        (TRUE, 'True'),
        (FALSE, 'False'),
    )

    discarded = django_filters.ChoiceFilter(
        field_name='discarded',
        label='discarded',
        choices=BOOLEAN_CHOICES,
        method='discarded_entry_filter'
    )

    class Meta:
        model = Entry
        fields = ('discarded',)

    def discarded_entry_filter(self, queryset, name, value):
        print("####", queryset)
        if value == self.TRUE:
            discarded_entries = DiscardedEntry.objects.filter(
                analysis_pillar=self.request.data.get('analysis_pillar_id')
            ).values('entry')
            return queryset.filter(id__in=discarded_entries)
        elif value == self.FALSE:
            discarded_entries = DiscardedEntry.objects.filter(
                analysis_pillar=self.request.data.get('analysis_pillar_id')
            ).values('entry')
            return queryset.exclude(id__in=discarded_entries)
        else:
            print(queryset)
            return queryset
        return queryset
