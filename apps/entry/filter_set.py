import copy
from functools import reduce
from datetime import datetime

import graphene
import django_filters
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates.general import ArrayAgg
from graphene_django.filter.filterset import GrapheneFilterSetMixin
from graphene_django.filter.utils import get_filtering_args_from_filterset

from user_resource.filters import UserResourceGqlFilterSet
from utils.common import is_valid_number
from utils.graphene.fields import (
    generate_simple_object_type_from_input_type,
    generate_object_field_from_input_type,
    compare_input_output_type_fields,
)
from utils.graphene.filters import (
    IDListFilter,
    MultipleInputFilter,
    DateGteFilter,
    DateLteFilter,
)
from deep.filter_set import DjangoFilterCSVWidget
from analysis_framework.models import Filter
from lead.models import Lead
from organization.models import OrganizationType
from analysis_framework.models import Widget
from geo.models import GeoArea
from quality_assurance.models import EntryReviewComment

from lead.enums import (
    LeadStatusEnum,
    LeadPriorityEnum,
    LeadConfidentialityEnum,
)
from entry.widgets.date_widget import parse_date_str
from entry.widgets.time_widget import parse_time_str

from .models import (
    Entry,
    EntryComment,
    ProjectEntryLabel,
)
from .enums import EntryTagTypeEnum


# TODO: Find out whether we need to call timezone.make_aware
# from django.utils module to all datetime objects below

# We don't use UserResourceFilterSet since created_at and modified_at
# are overridden below
class EntryFilterMixin(django_filters.filterset.FilterSet):
    """
    Entry filter set
    Basic filtering with lead, excerpt, lead title and dates
    """
    class CommentStatus(models.TextChoices):
        RESOLVED = 'resolved', 'Resolved',
        UNRESOLVED = 'unresolved', 'Unresolved',

    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
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
    lead_assignee = django_filters.ModelMultipleChoiceFilter(
        label='Lead Assignees',
        queryset=User.objects.all(),
        field_name='lead__assignee',
    )

    comment_status = django_filters.ChoiceFilter(
        label='Comment Status', choices=CommentStatus.choices, method='comment_status_filter',
    )
    comment_assignee = django_filters.ModelMultipleChoiceFilter(
        label='Comment Assignees',
        queryset=User.objects.all(),
        field_name='entrycomment__assignees',
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
    authoring_organization_types = django_filters.ModelMultipleChoiceFilter(
        method='authoring_organization_types_filter',
        widget=DjangoFilterCSVWidget,
        queryset=OrganizationType.objects.all(),
    )

    class Meta:
        model = Entry
        fields = {
            **{
                x: ['exact'] for x in [
                    'id', 'excerpt', 'lead__title', 'created_at',
                    'created_by', 'modified_at', 'modified_by', 'project',
                    'controlled',
                ]
            },
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            # 'lead_published_on': ['exact', 'lt', 'gt', 'lte', 'gte'],
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
        if value == self.CommentStatus.UNRESOLVED:
            return queryset.filter(
                entrycomment__is_resolved=False,
                entrycomment__parent__isnull=True,
            )
        elif value == self.CommentStatus.RESOLVED:
            return queryset.filter(
                entrycomment__is_resolved=True,
                entrycomment__parent__isnull=True,
            )
        return queryset

    def comment_created_by_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                entrycomment__created_by__in=value,
                entrycomment__parent__isnull=True,
            )
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
            return queryset.filter(query_params)
        return queryset

    def project_entry_labels_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                entrygrouplabel__label__in=value,
            )
        return queryset

    def lead_group_label_filter(self, queryset, name, value):
        if value:
            return queryset.filter(entrygrouplabel__group__title__icontains=value)
        return queryset

    def authoring_organization_types_filter(self, qs, name, value):
        if value:
            qs = qs.annotate(
                organization_types=models.functions.Coalesce(
                    'lead__authors__parent__organization_type',
                    'lead__authors__organization_type'
                )
            )
            if isinstance(value[0], OrganizationType):
                return qs.filter(organization_types__in=[ot.id for ot in value]).distinct()
            return qs.filter(organization_types__in=value).distinct()
        return qs

    @property
    def qs(self):
        qs = super().qs
        # Note: Since we cannot have `.distinct()` inside a subquery
        if self.data.get('from_subquery', False):
            return Entry.objects.filter(id__in=qs)
        return qs.distinct()


class EntryFilterSet(EntryFilterMixin, django_filters.rest_framework.FilterSet):
    class Meta:
        model = Entry
        fields = {
            **{
                x: ['exact'] for x in [
                    'id', 'excerpt', 'lead__title', 'created_at',
                    'created_by', 'modified_at', 'modified_by', 'project',
                    'controlled',
                ]
            },
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            # 'lead_published_on': ['exact', 'lt', 'gt', 'lte', 'gte'],
        }
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda _: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class EntryCommentFilterSet(django_filters.FilterSet):
    class Meta:
        model = EntryComment
        fields = ('created_by', 'is_resolved', 'resolved_at')


def get_filtered_entries_using_af_filter(
    entries, filters, queries,
    project=None, new_query_structure=False,
):
    queries = copy.deepcopy(queries)

    region_max_level = 0
    if project:
        region_max_level = project.regions\
            .annotate(adminlevel_count=models.Count('adminlevel'))\
            .aggregate(max_level=models.Max('adminlevel_count'))['max_level'] or 0

    if isinstance(queries, list):
        queries = {
            q['filter_key']: q
            for q in queries
        }
    elif 'filterable_data' in queries:
        # XXX: Pass new structure.
        queries = {
            q['filter_key']: q
            for q in queries['filterable_data']
        }
        new_query_structure = True

    # NOTE: lets not use `.distinct()` in this function as it is used by a subquery in `lead/models.py`.
    for _filter in filters:
        # For each filter, see if there is a query for that filter
        # and then perform filtering based on that query.

        use_exclude = False
        use_and_operator = False
        include_sub_regions = False

        if not new_query_structure:
            value = queries.get(_filter.key)
            value_lte = queries.get(_filter.key + '__lt')
            value_gte = queries.get(_filter.key + '__gt')
            value_and = queries.get(_filter.key + '__and')
            if value_and:
                value = value_and
                use_and_operator = True
                use_exclude = False
            value_exclude = queries.get(_filter.key + '_exclude')
            if value_exclude:
                value = value_exclude
                use_and_operator = False
                use_exclude = True
            value_exclude_and = queries.get(_filter.key + '_exclude_and')
            if value_exclude_and:
                value = value_exclude
                use_exclude = True
                use_and_operator = True
            value_list = value
        else:
            query = queries.get(_filter.key)
            if not query:
                continue

            value = query.get('value')
            value_gte = query.get('value_gte')
            value_lte = query.get('value_lte')
            value_list = [
                v for v in query.get('value_list') or []
                if v is not None
            ]
            use_exclude = query.get('use_exclude')
            use_and_operator = query.get('use_and_operator')
            include_sub_regions = query.get('include_sub_regions')

        if not any([value, value_gte, value_lte, value_list]):
            continue

        # Convert Date to number
        if _filter.widget_type in [
            Widget.WidgetType.DATE,
            Widget.WidgetType.DATE_RANGE,
        ]:
            value = value and parse_date_str(value)[1]
            value_gte = value_gte and parse_date_str(value_gte)[1]
            value_lte = value_lte and parse_date_str(value_lte)[1]

        # Convert Time to number
        elif _filter.widget_type in [
            Widget.WidgetType.TIME,
            Widget.WidgetType.TIME_RANGE,
        ]:
            value = value and parse_time_str(value)['time_val']
            value_gte = value_gte and parse_time_str(value_gte)['time_val']
            value_lte = value_lte and parse_time_str(value_lte)['time_val']

        if _filter.filter_type == Filter.FilterType.NUMBER:
            if value:
                entries = entries.filter(
                    filterdata__filter=_filter,
                    filterdata__number=value,
                )
            else:
                if value_lte:
                    entries = entries.filter(
                        filterdata__filter=_filter,
                        filterdata__number__lte=value_lte,
                    )
                if value_gte:
                    entries = entries.filter(
                        filterdata__filter=_filter,
                        filterdata__number__gte=value_gte,
                    )

        elif _filter.filter_type == Filter.FilterType.TEXT:
            if value:
                entries = entries.filter(
                    filterdata__filter=_filter,
                    filterdata__text__icontains=value,
                )

        elif _filter.filter_type == Filter.FilterType.INTERSECTS:
            if value:
                entries = entries.filter(
                    filterdata__filter=_filter,
                    filterdata__from_number__lte=value,
                    filterdata__to_number__gte=value,
                )

            if value_lte and value_gte:
                q = models.Q(
                    filterdata__from_number__lte=value_lte,
                    filterdata__to_number__gte=value_lte,
                ) | models.Q(
                    filterdata__from_number__lte=value_gte,
                    filterdata__to_number__gte=value_gte,
                ) | models.Q(
                    filterdata__from_number__gte=value_gte,
                    filterdata__to_number__lte=value_lte,
                )
                entries = entries.filter(q, filterdata__filter=_filter)

        elif _filter.filter_type == Filter.FilterType.LIST:
            if value_list and not isinstance(value_list, list):
                value_list = value_list.split(',')

            if value_list:
                # Fetch sub-regions if required
                if region_max_level and include_sub_regions and _filter.widget_type == Widget.WidgetType.GEO:
                    # XXX: simple values('id') doesn't work. Better way?
                    value_list = GeoArea.\
                        get_sub_childrens(value_list, level=region_max_level)\
                        .filter(admin_level__region__project=project)\
                        .order_by().values('admin_level__region__project')\
                        .annotate(ids=ArrayAgg('id'))\
                        .values('ids')

                query_filter = models.Q(
                    filterdata__filter=_filter,
                    # This will use <OR> filter
                    filterdata__values__overlap=value_list,
                )
                if use_and_operator:
                    query_filter = models.Q(
                        filterdata__filter=_filter,
                        # This will use <AND> filter
                        filterdata__values__contains=value_list,
                    )
                # Use filter to exclude entries
                if use_exclude:
                    entries = entries.exclude(query_filter)
                # Use filter to include entries
                else:
                    entries = entries.filter(query_filter)

    return entries.order_by('-lead__created_by', 'lead', 'created_by')


def get_filtered_entries(user, queries):
    # NOTE: lets not use `.distinct()` in this function as it is used by a
    # subquery in `lead/models.py`.
    entries = Entry.get_for(user)
    filters = Filter.get_for(user, with_widget_type=True)

    project_id = queries.get('project')
    if project_id:
        entries = entries.filter(lead__project__id=project_id)
        filters = filters.filter(analysis_framework__project__id=project_id)

    entries_id = queries.get('entries_id')
    if entries_id:
        entries = entries.filter(id__in=entries_id)

    entry_type = queries.get('entry_type')
    if entry_type:
        entries = entries.filter(entry_type__in=entry_type)

    lead_status = queries.get('lead_status')
    if lead_status:
        entries = entries.filter(lead__status__in=lead_status)

    lead_priority = queries.get('lead_priority')
    if lead_priority:
        entries = entries.filter(lead__priority__in=lead_priority)

    lead_confidentiality = queries.get('lead_confidentiality')
    if lead_confidentiality:
        entries = entries.filter(lead__confidentiality__in=lead_confidentiality)

    # Filter by filterset
    updated_queries = get_created_at_filters(queries)
    filterset = EntryFilterSet(data=updated_queries, queryset=entries)
    filterset.is_valid()  # This needs to be called
    entries = filterset.qs

    return get_filtered_entries_using_af_filter(entries, filters, queries)


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


class EntryFilterDataInputType(graphene.InputObjectType):
    """
    Behaviour for each type:
    - NUMBER (value or (value_lte or value_gte) are applied if provided)
        - value (exact match)
        - value_lte (lt match)
        - value_gte (gt match)
    - TEXT
        - value (icontains match)
    - INTERSECTS (Both are applied if provided) (For date range, send <timestamp/day>)
        - value (exact match)
        - value_lte, value_gte (range match if both are provided)
    - LIST
        - value_list (This is used to filter value)
        - include_sub_regions (Includes sub-regions as value_list <using value_list to generate>)
        - use_and_operator (Use AND to filter)
        - use_exclude (Exclude entry using filter value)
    """
    filter_key = graphene.ID(required=True)
    value = graphene.String(description='Valid for single value widgets')
    value_gte = graphene.String(description='Valid for range or single value widgets')
    value_lte = graphene.String(description='Valid for range or single value widgets')
    value_list = graphene.List(graphene.NonNull(graphene.String), description='Valid for list value widgets')
    use_exclude = graphene.Boolean(description='Only for array values')
    use_and_operator = graphene.Boolean(description='Used AND instead of OR')
    include_sub_regions = graphene.Boolean(description='Only valid for GEO widget values')


# ----------------------------- Graphql Filters ---------------------------------------
class EntryGQFilterSet(GrapheneFilterSetMixin, UserResourceGqlFilterSet):
    # Lead fields
    leads = IDListFilter(field_name='lead')
    lead_created_by = IDListFilter(field_name='lead__created_by')
    lead_published_on = django_filters.DateFilter()
    lead_published_on_gte = DateGteFilter(field_name='lead__published_on')
    lead_published_on_lte = DateLteFilter(field_name='lead__published_on')
    lead_title = django_filters.CharFilter(lookup_expr='icontains', field_name='lead__title')
    lead_assignees = IDListFilter(label='Lead Assignees', field_name='lead__assignee')
    lead_statuses = MultipleInputFilter(LeadStatusEnum, field_name='lead__status')
    lead_priorities = MultipleInputFilter(LeadPriorityEnum, field_name='lead__priority')
    lead_confidentialities = MultipleInputFilter(LeadConfidentialityEnum, field_name='lead__confidentiality')
    lead_authoring_organization_types = IDListFilter(method='authoring_organization_types_filter')
    lead_author_organizations = IDListFilter(field_name='lead__authors')
    lead_source_organizations = IDListFilter(field_name='lead__source')

    search = django_filters.CharFilter(method='search_filter')
    created_by = IDListFilter()
    modified_by = IDListFilter()
    entry_types = MultipleInputFilter(EntryTagTypeEnum, field_name='entry_type')
    project_entry_labels = IDListFilter(label='Project Entry Labels', method='project_entry_labels_filter')
    entries_id = IDListFilter(field_name='id')
    geo_custom_shape = django_filters.CharFilter(label='GEO Custom Shapes', method='geo_custom_shape_filter')
    # Entry Group Label Filters
    lead_group_label = django_filters.CharFilter(label='Lead Group Label', method='lead_group_label_filter')
    # Dynamic filterable data
    filterable_data = MultipleInputFilter(EntryFilterDataInputType, method='filterable_data_filter')
    has_comment = django_filters.BooleanFilter(method='filter_commented_entries')
    is_verified = django_filters.BooleanFilter(method='filter_verified_entries')

    class Meta:
        model = Entry
        fields = {
            **{
                x: ['exact'] for x in [
                    'id', 'excerpt', 'controlled',
                ]
            },
        }
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda _: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    def filterable_data_filter(self, queryset, _, value):
        if value:
            project = self.request and self.request.active_project
            if project is None or project.analysis_framework_id is None:
                # This needs to be defined
                raise Exception(f'Both should be defined {project=} {project and project.analysis_framework_id=}')
            filters = Filter.qs_with_widget_type().filter(analysis_framework_id=project.analysis_framework_id).all()
            return get_filtered_entries_using_af_filter(queryset, filters, value, project=project, new_query_structure=True)
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
            return queryset.filter(query_params)
        return queryset

    def project_entry_labels_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                entrygrouplabel__label__in=value,
            )
        return queryset

    def lead_group_label_filter(self, queryset, name, value):
        if value:
            return queryset.filter(entrygrouplabel__group__title__icontains=value)
        return queryset

    def authoring_organization_types_filter(self, qs, name, value):
        if value:
            qs = qs.annotate(
                organization_types=models.functions.Coalesce(
                    'lead__authors__parent__organization_type',
                    'lead__authors__organization_type'
                )
            )
            if isinstance(value[0], OrganizationType):
                return qs.filter(organization_types__in=[ot.id for ot in value]).distinct()
            return qs.filter(organization_types__in=value).distinct()
        return qs

    def filter_commented_entries(self, queryset, name, value):
        _filter = dict(
            review_comments__comment_type__in=[
                EntryReviewComment.CommentType.COMMENT,
                EntryReviewComment.CommentType.UNVERIFY,
                EntryReviewComment.CommentType.UNCONTROL,
            ]
        )
        if value:
            return queryset.filter(**_filter)
        return queryset.exclude(**_filter)

    def filter_verified_entries(self, queryset, name, value):
        if value:
            return queryset.filter(verified_by__isnull=False)
        return queryset.filter(verified_by__isnull=True)

    def search_filter(self, qs, _, value):
        if value:
            filters = models.Q(lead__title__icontains=value) | models.Q(excerpt__icontains=value)
            if is_valid_number(value):
                filters = models.Q(id=value) | filters
            return qs.filter(filters)
        return qs

    @property
    def qs(self):
        qs = super().qs
        # Note: Since we cannot have `.distinct()` inside a subquery
        if self.data.get('from_subquery', False):
            return Entry.objects.filter(id__in=qs)
        return qs.distinct()


def get_entry_filter_object_type(input_type):
    new_fields_map = generate_object_field_from_input_type(input_type, skip_fields=['filterable_data'])
    new_fields_map['filterable_data'] = graphene.List(
        graphene.NonNull(
            generate_simple_object_type_from_input_type(EntryFilterDataInputType)
        )
    )
    new_type = type('EntriesFilterDataType', (graphene.ObjectType,), new_fields_map)
    compare_input_output_type_fields(input_type, new_type)
    return new_type


EntriesFilterDataInputType = type(
    'EntriesFilterDataInputType',
    (graphene.InputObjectType,),
    get_filtering_args_from_filterset(EntryGQFilterSet, 'entry.schema.EntryListType')
)
EntriesFilterDataType = get_entry_filter_object_type(EntriesFilterDataInputType)
