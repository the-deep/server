import django_filters

from project.models import Project
from utils.graphene.filters import StringListFilter
from .models import Export


class ExportFilterSet(django_filters.rest_framework.FilterSet):
    """
    Export filter set
    Also make most fields filerable by multiple values
    """
    project = django_filters.ModelChoiceFilter(
        queryset=Project.objects.all(),
        field_name='project',
    )

    ordering = django_filters.CharFilter(
        method='ordering_filter',
    )

    status = django_filters.MultipleChoiceFilter(
        choices=Export.Status.choices,
        widget=django_filters.widgets.CSVWidget
    )

    type = django_filters.MultipleChoiceFilter(
        choices=Export.DataType.choices,
        widget=django_filters.widgets.CSVWidget
    )
    exported_at__lt = django_filters.DateFilter(
        field_name='exported_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z']
    )
    exported_at__gte = django_filters.DateFilter(
        field_name='exported_at',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d%z']
    )

    class Meta:
        model = Export
        fields = ['is_archived']

    def ordering_filter(self, qs, name, value):
        orderings = [x.strip() for x in value.split(',') if x.strip()]

        for ordering in orderings:
            qs = qs.order_by(ordering)
        return qs


class ExportGQLFilterSet(django_filters.rest_framework.FilterSet):
    type = StringListFilter(method='filter_by_type')
    status = StringListFilter(method='filter_by_status')

    class Meta:
        model = Export
        fields = ()

    def filter_by_type(self, qs, name, value):
        if value:
            return qs.filter(type__in=value).distinct()
        return qs

    def filter_by_status(self, qs, name, value):
        if value:
            return qs.filter(status__in=value).distinct()
        return qs
