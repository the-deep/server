import django_filters

from .models import Analysis


class AnalysisFilterSet(django_filters.FilterSet):
    created__lt = django_filters.DateFilter(
        field_name='created_on', lookup_expr='lt',
        input_formats=['%Y-%m-%d'],
    )
    created__gt = django_filters.DateFilter(
        field_name='created_on', lookup_expr='gt',
        input_formats=['%Y-%m-%d'],
    )
    created__lte = django_filters.DateFilter(
        field_name='created_on', lookup_expr='lte',
        input_formats=['%Y-%m-%d'],
    )
    created__gte = django_filters.DateFilter(
        field_name='created_on', lookup_expr='gte',
        input_formats=['%Y-%m-%d'],
    )
    created__gte = django_filters.DateFilter(
        field_name='created_on', lookup_expr='gte',
        input_formats=['%Y-%m-%d'],
    )
    created__exact = django_filters.DateFilter(
        field_name='created_on', lookup_expr='exact',
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        models = Analysis
        fields = ()
