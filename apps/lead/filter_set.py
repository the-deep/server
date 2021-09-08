import django_filters
import graphene
from django.db import models
from graphene_django.filter.utils import get_filtering_args_from_filterset

from deep.filter_set import DjangoFilterCSVWidget
from user_resource.filters import UserResourceFilterSet
from utils.graphene.filters import (
    NumberInFilter,
    MultipleInputFilter,
    SimpleInputFilter,
    IDListFilter,
)
from utils.graphene.enums import convert_enum_to_graphene_enum

from project.models import Project
from organization.models import OrganizationType
from user.models import User
from entry.filter_set import get_filtered_entries, EntryGQFilterSet
# from entry.schema import EntryListType

from .models import Lead, LeadGroup
from .enums import (
    LeadConfidentialityEnum,
    LeadStatusEnum,
    LeadPriorityEnum,
    LeadSourceTypeEnum,
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
            'exclude_empty_controlled_filtered_entries',
            'exclude empty controlled filtered entries',
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
                for x in ['id', 'text', 'url', 'website']
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
            models.Q(url__icontains=value) |
            models.Q(website__icontains=value)
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
                organization_types=models.functions.Coalesce(
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
class LeadGQFilterSet(LeadFilterSet):
    ordering = None
    project = None
    assignee = None
    priority = None
    status = None

    source_types = MultipleInputFilter(LeadSourceTypeEnum, field_name='source_type')
    priorities = MultipleInputFilter(LeadPriorityEnum, field_name='priority')
    confidentiality = SimpleInputFilter(LeadConfidentialityEnum)
    statuses = MultipleInputFilter(LeadStatusEnum, field_name='status')
    assignees = IDListFilter(field_name='assignee')
    authoring_organization_types = IDListFilter(method='authoring_organization_types_filter')
    # Filter-only enum filter
    exists = SimpleInputFilter(
        convert_enum_to_graphene_enum(LeadFilterSet.Exists, name='LeadExistsEnum'),
        label='Exists Choice', method='exists_filter',
    )
    custom_filters = SimpleInputFilter(
        convert_enum_to_graphene_enum(LeadFilterSet.CustomFilter, name='LeadCustomFilterEnum'),
        label='Filtered Exists Choice', method='filtered_exists_filter',
    )
    entries_filter_data = SimpleInputFilter(
        type(
            'LeadEntriesFilterData',
            (graphene.InputObjectType,),
            get_filtering_args_from_filterset(EntryGQFilterSet, 'entry.schema.EntryListType')
        ),
        method='filtered_entries_filter_data'
    )

    def filtered_entries_filter_data(self, qs, name, value):
        # NOTE: This filter data is used by filtered_exists_filter
        return qs

    def filtered_exists_filter(self, qs, name, value):
        entries_filter_data = self.data.get('entries_filter_data') or {}

        def _get_annotate(**filters):
            return models.functions.Coalesce(
                models.Subquery(
                    get_filtered_entries(self.request.user, entries_filter_data).filter(
                        lead=models.OuterRef('pk'),
                        **filters,
                    ).values('lead').order_by().annotate(
                        count=models.Count('id')
                    ).values('count')[:1], output_field=models.IntegerField()
                ), 0
            )

        if value == self.CustomFilter.EXCLUDE_EMPTY_FILTERED_ENTRIES:
            return qs.annotate(filtered_entries_count=_get_annotate()).filter(filtered_entries_count__gte=1)
        elif value == self.CustomFilter.EXCLUDE_EMPTY_CONTROLLED_FILTERED_ENTRIES:
            return qs.annotate(filtered_entries_count=_get_annotate(controlled=True)).filter(filtered_entries_count__gte=1)
        return qs
