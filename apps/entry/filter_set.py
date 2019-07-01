from django.db import models
from django.contrib.auth.models import User

from analysis_framework.models import Filter
from lead.models import Lead
from entry.models import Entry

import django_filters

from datetime import datetime


# TODO: Find out whether we need to call timezone.make_aware
# from django.utils module to all datetime objects below


# We don't use UserResourceFilterSet since created_at and modified_at
# are overridden below
class EntryFilterSet(django_filters.FilterSet):
    """
    Entry filter set

    Basic filtering with lead, excerpt, lead title and dates
    """
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
    )
    lead__published_on__lt = django_filters.DateFilter(
        field_name='lead__published_on', lookup_expr='lte',
    )
    lead__published_on__gt = django_filters.DateFilter(
        field_name='lead__published_on', lookup_expr='gte',
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
    )
    modified_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
    )

    class Meta:
        model = Entry
        fields = [
            'id', 'excerpt', 'lead__title', 'created_at', 'created_by', 'modified_at', 'modified_by', 'project',
        ]
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


def get_filtered_entries(user, queries):
    entries = Entry.get_for(user)
    project = queries.get('project')
    if project:
        entries = entries.filter(lead__project__id=project)

    filters = Filter.get_for(user)
    if project:
        filters = filters.filter(analysis_framework__project__id=project)

    ONE_DAY = 24 * 60 * 60

    created_at__lt = queries.get('created_at__lt')
    if created_at__lt:
        created_at__lt = datetime.fromtimestamp(created_at__lt * ONE_DAY)
        entries = entries.filter(created_at__lte=created_at__lt)

    created_at__gt = queries.get('created_at__gt')
    if created_at__gt:
        created_at__gt = datetime.fromtimestamp(created_at__gt * ONE_DAY)
        entries = entries.filter(created_at__gte=created_at__gt)

    modified_at__lt = queries.get('modified_at__lt')
    if modified_at__lt:
        modified_at__lt = datetime.fromtimestamp(modified_at__lt * ONE_DAY)
        entries = entries.filter(modified_at__lte=modified_at__lt)

    modified_at__gt = queries.get('modified_at__gt')
    if modified_at__gt:
        modified_at__gt = datetime.fromtimestamp(modified_at__gt * ONE_DAY)
        entries = entries.filter(modified_at__gte=modified_at__gt)

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

        if filter.filter_type == Filter.INTERSECTS:
            if query:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__from_number__lte=query,
                    filterdata__to_number__gte=query,
                )

            if query_lt and query_gt:
                q = models.Q(
                    filterdata__from_number__lte=query_lt,
                    filterdata__to_number__gte=query_lt,
                ) | models.Q(
                    filterdata__from_number__lte=query_gt,
                    filterdata__to_number__gte=query_gt,
                ) | models.Q(
                    filterdata__from_number__gte=query_gt,
                    filterdata__to_number__lte=query_lt,
                )
                entries = entries.filter(q, filterdata__filter=filter)

        if filter.filter_type == Filter.LIST and query:
            if not isinstance(query, list):
                query = query.split(',')

            if len(query) > 0:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__values__overlap=query,
                )

    return entries.order_by('-lead__created_by', 'lead', 'created_by')
