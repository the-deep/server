import graphene
import django_filters
from django.db import models
from django.db.models.functions import Coalesce
from graphene_django.filter.utils import get_filtering_args_from_filterset

from deep.filter_set import DjangoFilterCSVWidget
from user_resource.filters import UserResourceFilterSet
from utils.graphene.filters import (
    NumberInFilter,
    MultipleInputFilter,
    SimpleInputFilter,
    IDListFilter,
    DateGteFilter,
    DateLteFilter,
)

from project.models import Project
from organization.models import OrganizationType
from user.models import User
from entry.models import Entry
from entry.filter_set import EntryGQFilterSet, EntriesFilterDataType
from user_resource.filters import UserResourceGqlFilterSet

from .models import Lead, LeadGroup
from .enums import (
    LeadConfidentialityEnum,
    LeadStatusEnum,
    LeadPriorityEnum,
    LeadSourceTypeEnum,
    LeadOrderingEnum,
    LeadExtractionStatusEnum,
)


class LeadFilterSet(django_filters.FilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """

    class Exists(models.TextChoices):
        ENTRIES_EXISTS = 'entries_exists', 'Entry Exists'
        ASSESSMENT_EXISTS = 'assessment_exists', 'Assessment Exists'
        ENTRIES_DO_NOT_EXIST = 'entries_do_not_exist', 'Entries do not exist'
        ASSESSMENT_DOES_NOT_EXIST = 'assessment_does_not_exist', 'Assessment does not exist'

    class CustomFilter(models.TextChoices):
        EXCLUDE_EMPTY_FILTERED_ENTRIES = 'exclude_empty_filtered_entries', 'exclude empty filtered entries'
        EXCLUDE_EMPTY_CONTROLLED_FILTERED_ENTRIES = (
            'exclude_empty_controlled_filtered_entries', 'exclude empty controlled filtered entries'
        )

    search = django_filters.CharFilter(method='search_filter')

    published_on__lt = django_filters.DateFilter(
        field_name='published_on', lookup_expr='lt',
    )
    published_on__gt = django_filters.DateFilter(
        field_name='published_on', lookup_expr='gt',
    )
    published_on__lte = django_filters.DateFilter(
        field_name='published_on', lookup_expr='lte',
    )
    published_on__gte = django_filters.DateFilter(
        field_name='published_on', lookup_expr='gte',
    )
    project = django_filters.CharFilter(
        method='project_filter',
    )
    confidentiality = django_filters.MultipleChoiceFilter(
        choices=Lead.Confidentiality.choices,
        widget=django_filters.widgets.CSVWidget,
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Lead.Status.choices,
        widget=django_filters.widgets.CSVWidget,
    )
    priority = django_filters.MultipleChoiceFilter(
        choices=Lead.Priority.choices,
        widget=django_filters.widgets.CSVWidget,
    )
    assignee = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=django_filters.widgets.CSVWidget,
    )
    classified_doc_id = NumberInFilter(
        field_name='leadpreview__classified_doc_id',
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    created_at = django_filters.DateTimeFilter(
        field_name='created_at',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__lt = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lt',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte',
        input_formats=['%Y-%m-%d%z'],
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z'],
    )
    exists = django_filters.ChoiceFilter(
        label='Exists Choice',
        choices=Exists.choices, method='exists_filter',
    )

    emm_entities = django_filters.CharFilter(
        method='emm_entities_filter',
    )

    emm_keywords = django_filters.CharFilter(
        method='emm_keywords_filter',
    )

    emm_risk_factors = django_filters.CharFilter(
        method='emm_risk_factors_filter',
    )

    ordering = django_filters.CharFilter(
        method='ordering_filter',
    )

    authoring_organization_types = django_filters.ModelMultipleChoiceFilter(
        method='authoring_organization_types_filter',
        widget=DjangoFilterCSVWidget,
        queryset=OrganizationType.objects.all(),
    )
    # used in export
    custom_filters = django_filters.ChoiceFilter(
        label='Filtered Exists Choice',
        choices=CustomFilter.choices, method='filtered_exists_filter',
    )

    class Meta:
        model = Lead
        fields = {
            **{
                x: ['exact']
                for x in ['id', 'text', 'url']
            },
            'emm_entities': ['exact'],
            # 'emm_keywords': ['exact'],
            # 'emm_risk_factors': ['exact'],
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'published_on': ['exact', 'lt', 'gt', 'lte', 'gte'],
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    @staticmethod
    def get_processed_filter_data(raw_filter_data):
        """Make json data usable by filterset class.
        This basically processes list query_params and joins them to comma separated string.
        """
        filter_data = {}
        for key, value in raw_filter_data.items():
            if isinstance(value, list):
                filter_data[key] = ','.join([str(x) for x in value])
            else:
                filter_data[key] = value
        return filter_data

    def search_filter(self, qs, name, value):
        # NOTE: This exists to make it compatible with post filter
        if not value:
            return qs
        return qs.filter(
            # By title
            models.Q(title__icontains=value) |
            # By source
            models.Q(source_raw__icontains=value) |
            models.Q(source__title__icontains=value) |
            models.Q(source__parent__title__icontains=value) |
            # By author
            models.Q(author__title__icontains=value) |
            models.Q(author__parent__title__icontains=value) |
            models.Q(author_raw__icontains=value) |
            models.Q(authors__title__icontains=value) |
            models.Q(authors__parent__title__icontains=value) |
            # By URL
            models.Q(url__icontains=value)
        ).distinct()

    def project_filter(self, qs, name, value):
        # NOTE: @bewakes used this because normal project filter
        # was giving problem with post filter
        project_ids = value.split(',')
        return qs.filter(project_id__in=project_ids)

    def exists_filter(self, qs, name, value):
        if value == self.Exists.ENTRIES_EXISTS:
            return qs.filter(entry__isnull=False)
        elif value == self.Exists.ASSESSMENT_EXISTS:
            return qs.filter(assessment__isnull=False)
        elif value == self.Exists.ENTRIES_DO_NOT_EXIST:
            return qs.filter(entry__isnull=True)
        elif value == self.Exists.ASSESSMENT_DOES_NOT_EXIST:
            return qs.filter(assessment__isnull=True)
        return qs

    def emm_entities_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_entities__in=splitted)

    def emm_keywords_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_triggers__emm_keyword__in=splitted)

    def emm_risk_factors_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_triggers__emm_risk_factor__in=splitted)

    def ordering_filter(self, qs, name, value):
        # NOTE: @bewakes used this because normal ordering filter
        # was giving problem with post filter
        # Just clean the order_by fields
        orderings = [x.strip() for x in value.split(',') if x.strip()]

        for ordering in orderings:
            if ordering == '-page_count':
                qs = qs.order_by(models.F('leadpreview__page_count').desc(nulls_last=True))
            elif ordering == 'page_count':
                qs = qs.order_by(models.F('leadpreview__page_count').asc(nulls_first=True))
            else:
                qs = qs.order_by(ordering)
        return qs

    def authoring_organization_types_filter(self, qs, name, value):
        if value:
            qs = qs.annotate(
                organization_types=Coalesce(
                    'authors__parent__organization_type',
                    'authors__organization_type'
                )
            )
            if type(value[0]) == OrganizationType:
                return qs.filter(organization_types__in=[ot.id for ot in value]).distinct()
            return qs.filter(organization_types__in=value).distinct()
        return qs

    def filtered_exists_filter(self, qs, name, value):
        # NOTE: check annotations at Lead.get_for
        if value == self.CustomFilter.EXCLUDE_EMPTY_FILTERED_ENTRIES:
            return qs.filter(filtered_entries_count__gte=1)
        elif value == self.CustomFilter.EXCLUDE_EMPTY_CONTROLLED_FILTERED_ENTRIES:
            return qs.filter(controlled_filtered_entries_count__gte=1)
        return qs

    @property
    def qs(self):
        return super().qs.distinct()


class LeadGroupFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = LeadGroup
        fields = ['id', 'title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


# ------------------------------ Graphql filters -----------------------------------
class LeadGQFilterSet(UserResourceGqlFilterSet):
    ids = IDListFilter(method='filter_leads_id', help_text='Empty ids are ignored.')
    exclude_provided_leads_id = django_filters.BooleanFilter(
        method='filter_exclude_provided_leads_id', help_text='Only used when ids are provided.')
    created_by = IDListFilter()
    modified_by = IDListFilter()
    source_types = MultipleInputFilter(LeadSourceTypeEnum, field_name='source_type')
    priorities = MultipleInputFilter(LeadPriorityEnum, field_name='priority')
    confidentiality = SimpleInputFilter(LeadConfidentialityEnum)
    statuses = MultipleInputFilter(LeadStatusEnum, field_name='status')
    extraction_status = SimpleInputFilter(LeadExtractionStatusEnum, field_name='extraction_status')
    assignees = IDListFilter(field_name='assignee')
    authoring_organization_types = IDListFilter(method='authoring_organization_types_filter')
    author_organizations = IDListFilter(method='authoring_organizations_filter')
    source_organizations = IDListFilter(method='source_organizations_filter')
    # Filter-only enum filter
    has_entries = django_filters.BooleanFilter(method='filter_has_entries', help_text='Lead has entries.')
    has_assessment = django_filters.BooleanFilter(method='filter_has_assessment', help_text='Lead has assessment.')
    entries_filter_data = SimpleInputFilter(EntriesFilterDataType, method='filtered_entries_filter_data')

    search = django_filters.CharFilter(method='search_filter')

    published_on = django_filters.DateFilter()
    published_on_gte = DateGteFilter(field_name='published_on')
    published_on_lte = DateLteFilter(field_name='published_on')

    emm_entities = django_filters.CharFilter(method='emm_entities_filter')
    emm_keywords = django_filters.CharFilter(method='emm_keywords_filter')
    emm_risk_factors = django_filters.CharFilter(method='emm_risk_factors_filter')

    ordering = MultipleInputFilter(LeadOrderingEnum, method='ordering_filter')

    class Meta:
        model = Lead
        fields = {
            **{
                x: ['exact']
                for x in ['text', 'url']
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_context = {}

    @property
    def active_project(self) -> Project:
        if self.request is None:
            raise Exception(f'{self.request=} should be defined')
        if self.request.active_project is None:
            raise Exception(f'{self.request.active_project=} should be defined')
        return self.request.active_project

    @staticmethod
    def get_dummy_request(project):
        """
        Use this if request is not available
        """
        return type('DummyRequest', (object,), dict(active_project=project))()

    # Filters methods
    def search_filter(self, qs, name, value):
        # NOTE: This exists to make it compatible with post filter
        if not value:
            return qs
        return qs.filter(
            # By title
            models.Q(title__icontains=value) |
            # By source
            models.Q(source_raw__icontains=value) |
            models.Q(source__title__icontains=value) |
            models.Q(source__parent__title__icontains=value) |
            # By author
            models.Q(author__title__icontains=value) |
            models.Q(author__parent__title__icontains=value) |
            models.Q(author_raw__icontains=value) |
            models.Q(authors__title__icontains=value) |
            models.Q(authors__parent__title__icontains=value) |
            # By URL
            models.Q(url__icontains=value)
        ).distinct()

    def ordering_filter(self, qs, name, value):
        active_entry_count_field = self.custom_context.get('active_entry_count_field')
        for ordering in value:
            # Custom for entries count (use filter or normal entry count)
            if active_entry_count_field and ordering in [
                LeadOrderingEnum.ASC_ENTRIES_COUNT,
                LeadOrderingEnum.DESC_ENTRIES_COUNT,
            ]:
                if ordering == LeadOrderingEnum.ASC_ENTRIES_COUNT:
                    qs = qs.order_by(active_entry_count_field)
                else:
                    qs = qs.order_by(f'-{active_entry_count_field}')
            # Custom for page count with nulls_last
            elif ordering == LeadOrderingEnum.DESC_PAGE_COUNT:
                qs = qs.order_by(models.F('leadpreview__page_count').desc(nulls_last=True))
            elif ordering == LeadOrderingEnum.ASC_PAGE_COUNT:
                qs = qs.order_by(models.F('leadpreview__page_count').asc(nulls_first=True))
            # For remaining
            else:
                qs = qs.order_by(ordering)
        return qs

    def emm_entities_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_entities__in=splitted)

    def emm_keywords_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_triggers__emm_keyword__in=splitted)

    def emm_risk_factors_filter(self, qs, name, value):
        splitted = [x for x in value.split(',') if x]
        return qs.filter(emm_triggers__emm_risk_factor__in=splitted)

    def authoring_organization_types_filter(self, qs, name, value):
        if value:
            qs = qs.annotate(
                organization_types=Coalesce(
                    'authors__parent__organization_type',
                    'authors__organization_type'
                )
            )
            if type(value[0]) == OrganizationType:
                return qs.filter(organization_types__in=[ot.id for ot in value]).distinct()
            return qs.filter(organization_types__in=value).distinct()
        return qs

    def authoring_organizations_filter(self, qs, _, value):
        if value:
            qs = qs.annotate(authoring_organizations=Coalesce('authors__parent_id', 'authors__id'))
            return qs.filter(authoring_organizations__in=value).distinct()
        return qs

    def source_organizations_filter(self, qs, _, value):
        if value:
            qs = qs.annotate(source_organizations=Coalesce('source__parent_id', 'source__id'))
            return qs.filter(source_organizations__in=value).distinct()
        return qs

    def filter_exclude_provided_leads_id(self, qs, *_):
        # NOTE: Used in filter_leads_id
        return qs

    def filter_leads_id(self, qs, _, value):
        if value is None:
            return qs
        if self.data.get('exclude_provided_leads_id'):
            return qs.exclude(id__in=value)
        return qs.filter(id__in=value)

    def filter_has_entries(self, qs, _, value):
        if value is None:
            return qs
        if value:
            return qs.filter(entry_count__gt=0)
        return qs.filter(entry_count=0)

    def filter_has_assessment(self, qs, _, value):
        if value is None:
            return qs
        return qs.filter(assessment__isnull=not value)

    def filtered_entries_filter_data(self, qs, _, value):
        if value is None:
            return qs
        return qs.filter(filtered_entry_count__gt=0)

    def filter_queryset(self, qs):
        def _entry_subquery(entry_qs: models.QuerySet):
            subquery_qs = entry_qs.\
                filter(
                    project=self.active_project,
                    analysis_framework=self.active_project.analysis_framework_id,
                    lead=models.OuterRef('pk'),
                )\
                .values('lead').order_by()\
                .annotate(count=models.Count('id'))\
                .values('count')
            return Coalesce(
                models.Subquery(
                    subquery_qs[:1],
                    output_field=models.IntegerField()
                ), 0,
            )

        # Pre-annotate required fields for entries count (w/wo filters)
        entries_filter_data = self.data.get('entries_filter_data')
        has_entries = self.data.get('has_entries')
        has_entries_count_ordering = any(
            ordering in [
                LeadOrderingEnum.ASC_ENTRIES_COUNT,
                LeadOrderingEnum.DESC_ENTRIES_COUNT,
            ] for ordering in self.data.get('ordering') or []
        )

        # With filter
        if entries_filter_data is not None:
            qs = qs.annotate(
                filtered_entry_count=_entry_subquery(
                    EntryGQFilterSet(
                        data={
                            **entries_filter_data,
                            'from_subquery': True,
                        },
                        request=self.request,
                    ).qs
                )
            )
            self.custom_context['active_entry_count_field'] = 'filtered_entry_count'
        # Without filter
        if has_entries is not None or (
            entries_filter_data is None and has_entries_count_ordering
        ):
            self.custom_context['active_entry_count_field'] = self.custom_context.\
                get('active_entry_count_field', 'entry_count')
            qs = qs.annotate(
                entry_count=_entry_subquery(Entry.objects.all())
            )
        # Call super function
        return super().filter_queryset(qs)

    @property
    def qs(self):
        return super().qs.distinct()


class LeadGroupGQFilterSet(UserResourceGqlFilterSet):
    search = django_filters.CharFilter(method='filter_title')

    class Meta:
        model = LeadGroup
        fields = ()

    def filter_title(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(title__icontains=value).distinct()


LeadsFilterDataType = type(
    'LeadsFilterDataType',
    (graphene.InputObjectType,),
    get_filtering_args_from_filterset(LeadGQFilterSet, 'lead.schema.LeadListType')
)
