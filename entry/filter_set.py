from django.db import models
from user_resource.filters import UserResourceFilterSet

from analysis_framework.models import Filter
from lead.models import Lead
from entry.models import Entry

import django_filters


class EntryFilterSet(UserResourceFilterSet):
    """
    Entry filter set

    Basic filtering with lead, excerpt, lead title and dates
    """
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    lead__published_on__lte = django_filters.DateFilter(
        name='lead__published_on', lookup_expr='lte',
    )
    lead__published_on__gte = django_filters.DateFilter(
        name='lead__published_on', lookup_expr='gte',
    )

    class Meta:
        model = Entry
        fields = ['id', 'excerpt', 'lead__title',
                  'created_at', 'created_by', 'modified_at', 'modified_by']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


def get_filtered_entries(user, queries):
    """
    Get queryset of entries based on dynamic filters
    """
    entries = Entry.get_for(user)
    project = queries.get('project')
    if project:
        entries = entries.filter(lead__project__id=project)

    filters = Filter.get_for(user)

    for filter in filters:
        # For each filter, see if there is a query for that filter
        # and then perform filtering based on that query.

        query = queries.get(filter.key)
        query_lt = queries.get(
            filter.key + '__lt'
        )
        query_gt = queries.get(
            filter.key + '__gt'
        )

        if filter.filter_type == Filter.NUMBER:
            if query:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__number=query,
                )
            if query_lt:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__number__lte=query_lt,
                )
            if query_gt:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__number__gte=query_gt,
                )

        if filter.filter_type == Filter.LIST and query:
            if not isinstance(query, list):
                query = query.split(',')

            if len(query) > 0:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__values__overlap=query,
                )

    return entries.order_by('-lead__created_by', 'lead')
