import django_filters

from .models import Analysis


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
        models = Analysis
        fields = ()
