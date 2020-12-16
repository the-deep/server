from functools import reduce
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
import django_filters

from deep.filter_set import DjangoFilterCSVWidget
from analysis_framework.models import Filter
from lead.models import Lead
from entry.models import (
    Entry,
    EntryComment,
    ProjectEntryLabel,
)
from organization.models import OrganizationType


# TODO: Find out whether we need to call timezone.make_aware
# from django.utils module to all datetime objects below

# We don't use UserResourceFilterSet since created_at and modified_at
# are overridden below
class EntryFilterSet(django_filters.rest_framework.FilterSet):
    """
    Entry filter set
    Basic filtering with lead, excerpt, lead title and dates
    """
    RESOLVED = 'resolved'
    UNRESOLVED = 'unresolved'
    COMMENT_STATUS = (
        (RESOLVED, 'Resolved'),
        (UNRESOLVED, 'Unresolved'),
    )

    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
    )
    modified_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
    )

    created_at = django_filters.DateTimeFilter(
        field_name='created_at',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__gt = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gt',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__lt = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lt',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z'],
    )

    lead_published_on = django_filters.DateFilter(
        field_name='lead__published_on',

    )
    lead_published_on__gt = django_filters.DateFilter(
        field_name='lead__published_on',
        lookup_expr='gt',

    )
    lead_published_on__lt = django_filters.DateFilter(
        field_name='lead__published_on',
        lookup_expr='lt',

    )
    lead_published_on__gte = django_filters.DateFilter(
        field_name='lead__published_on',
        lookup_expr='gte',

    )
    lead_published_on__lte = django_filters.DateFilter(
        field_name='lead__published_on',
        lookup_expr='lte',

    )

    comment_status = django_filters.ChoiceFilter(
        label='Comment Status',
        choices=COMMENT_STATUS, method='comment_status_filter',
    )
    comment_assignee = django_filters.ModelMultipleChoiceFilter(
        label='Comment Assignees',
        queryset=User.objects.all(),
        field_name='entrycomment__assignees', lookup_expr='in',
    )
    comment_created_by = django_filters.ModelMultipleChoiceFilter(
        label='Comment Created by',
        queryset=User.objects.all(), method='comment_created_by_filter',
    )

    geo_custom_shape = django_filters.CharFilter(
        label='GEO Custom Shapes',
        method='geo_custom_shape_filter',
    )

    # Entry Group Label Filters
    project_entry_labels = django_filters.ModelMultipleChoiceFilter(
        label='Project Entry Labels',
        queryset=ProjectEntryLabel.objects.all(), method='project_entry_labels_filter',
    )
    lead_group_label = django_filters.CharFilter(
        label='Lead Group Label',
        method='lead_group_label_filter',
    )
    authoring_organization_types = django_filters.CharFilter(
        method='authoring_organization_types_filter'
    )

    class Meta:
        model = Entry
        fields = {
            **{
                x: ['exact'] for x in [
                    'id', 'excerpt', 'lead__title', 'created_at',
                    'created_by', 'modified_at', 'modified_by', 'project',
                    'verified',
                ]
            },
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'lead_published_on': ['exact', 'lt', 'gt', 'lte', 'gte'],
        }
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    def comment_status_filter(self, queryset, name, value):
        if value == self.UNRESOLVED:
            return queryset.filter(
                entrycomment__is_resolved=False,
                entrycomment__parent__isnull=True,
            ).distinct()
        elif value == self.RESOLVED:
            return queryset.filter(
                entrycomment__is_resolved=True,
                entrycomment__parent__isnull=True,
            ).distinct()
        return queryset

    def comment_created_by_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                entrycomment__created_by__in=value,
                entrycomment__parent__isnull=True,
            ).distinct()
        return queryset

    def geo_custom_shape_filter(self, queryset, name, value):
        if value:
            query_params = reduce(
                lambda acc, item: acc | item,
                [
                    models.Q(
                        attribute__widget__widget_id='geoWidget',
                        attribute__data__value__contains=[{'type': v}],
                    ) for v in value.split(',')
                ],
            )
            return queryset.filter(query_params).distinct()
        return queryset

    def project_entry_labels_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                entrygrouplabel__label__in=value,
            ).distinct()
        return queryset

    def lead_group_label_filter(self, queryset, name, value):
        if value:
            return queryset.filter(entrygrouplabel__group__title__icontains=value).distinct()
        return queryset

    def authoring_organization_types_filter(self, queryset, name, value):
        splitted = [x for x in value.split(',') if x]
        if splitted:
            queryset = queryset.annotate(
                organization_types=models.functions.Coalesce(
                    'lead__authors__parent__organization_type',
                    'lead__authors__organization_type'
                )
            )
            return queryset.filter(organization_types__in=splitted).distinct()
        return queryset


class EntryCommentFilterSet(django_filters.FilterSet):
    class Meta:
        model = EntryComment
        fields = ('entry',)


def get_filtered_entries(user, queries):
    entries = Entry.get_for(user)
    project = queries.get('project')

    if project:
        entries = entries.filter(lead__project__id=project)

    lead_status = queries.get('lead_status')
    if lead_status:
        entries = entries.filter(lead__status__in=lead_status)

    lead_priority = queries.get('lead_priority')
    if lead_priority:
        entries = entries.filter(lead__priority__in=lead_priority)

    entry_type = queries.get('entry_type')
    if entry_type:
        entries = entries.filter(entry_type__in=entry_type)

    lead_confidentiality = queries.get('lead_confidentiality')
    if lead_confidentiality:
        entries = entries.filter(lead__confidentiality__in=lead_confidentiality)

    # Filter by filterset
    updated_queries = get_created_at_filters(queries)
    filterset = EntryFilterSet(data=updated_queries, queryset=entries)
    filterset.is_valid()  # This needs to be called
    entries = filterset.qs

    filters = Filter.get_for(user)
    if project:
        filters = filters.filter(analysis_framework__project__id=project)

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
        query_and = queries.get(
            filter.key + '__and'
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

        elif filter.filter_type == Filter.TEXT:
            if query:
                entries = entries.filter(
                    filterdata__filter=filter,
                    filterdata__text__icontains=query,
                )

        elif filter.filter_type == Filter.INTERSECTS:
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

        elif filter.filter_type == Filter.LIST:
            # query and query_and are mutual exclusive and query_and has higher priority
            query = query_and or query
            if query and not isinstance(query, list):
                query = query.split(',')

            if query and len(query) > 0:
                # Use contains (AND) filter if query_and was defined
                if query_and:
                    entries = entries.filter(
                        filterdata__filter=filter,
                        filterdata__values__contains=query,
                    )
                # Use overlap (OR) filter if query is only defined
                elif query:
                    entries = entries.filter(
                        filterdata__filter=filter,
                        filterdata__values__overlap=query,
                    )

    return entries.order_by('-lead__created_by', 'lead', 'created_by')


def parse_date(val):
    try:
        val = val.replace(':', '')
        return datetime.strptime(val, '%Y-%m-%d%z')
    except Exception:
        return None


QUERY_MAP = {
    'created_at': parse_date,
    'created_at__gt': parse_date,
    'created_at__lt': parse_date,
    'created_at__gte': parse_date,
    'created_at__lte': parse_date,
    'lead__published_on': parse_date,
    'lead__published_on__gt': parse_date,
    'lead__published_on__lt': parse_date,
    'lead__published_on__gte': parse_date,
    'lead__published_on__lte': parse_date,
}


def get_created_at_filters(query_params):
    """
    Convert created_at related query values to date objects to be later used
    by the filterset
    """
    parsed_query = {}
    for k, v in query_params.items():
        parse_func = QUERY_MAP.get(k)
        if parse_func:
            parsed_query[k] = parse_func(v)
        else:
            parsed_query[k] = v
    return parsed_query
