import django_filters

from project.models import Project
from .models import Export


class ExportFilterSet(django_filters.rest_framework.FilterSet):
    """
    Export filter set
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """
    project = django_filters.ModelChoiceFilter(
        queryset=Project.objects.all(),
        field_name='project',
    )

    ordering = django_filters.CharFilter(
        method='ordering_filter',
    )

    class Meta:
        model = Export
        fields = ['is_preview']

    def ordering_filter(self, qs, name, value):
        orderings = [x.strip() for x in value.split(',') if x.strip()]

        for ordering in orderings:
            qs = qs.order_by(ordering)
        return qs
