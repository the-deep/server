from django.db import models
import django_filters

from deep.filter_set import DjangoFilterCSVWidget
from user_resource.filters import UserResourceFilterSet
from project.models import Project
from organization.models import OrganizationType
from user.models import User
from .models import Lead, LeadGroup


class NumberInFilter(django_filters.BaseInFilter,
                     django_filters.NumberFilter):
    pass


class LeadFilterSet(django_filters.FilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """

    ENTRIES_EXIST = 'entries_exists'
    ASSESSMENT_EXISTS = 'assessment_exists'
    ENTRIES_DO_NOT_EXIST = 'entries_do_not_exist'
    ASSESSMENT_DOES_NOT_EXIST = 'assessment_does_not_exist'
    EXISTS_CHOICE = (
        (ENTRIES_EXIST, 'Entry Exists'),
        (ASSESSMENT_EXISTS, 'Assessment Exists'),
        (ENTRIES_DO_NOT_EXIST, 'Entries do not exist'),
        (ASSESSMENT_DOES_NOT_EXIST, 'Assessment does not exist'),
    )
    EXCLUDE_EMPTY_FILTERED_ENTRIES = 'exclude_empty_filtered_entries'
    EXCLUDE_EMPTY_VERIFIED_FILTERED_ENTRIES = 'exclude_empty_verified_filtered_entries'
    FILTERED_ENTRIES_CHOICE = (
        (EXCLUDE_EMPTY_FILTERED_ENTRIES, 'exclude empty filtered entries'),
        (EXCLUDE_EMPTY_VERIFIED_FILTERED_ENTRIES, 'exclude empty verified filtered entries'),
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
        choices=Lead.CONFIDENTIALITIES,
        widget=django_filters.widgets.CSVWidget,
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Lead.STATUSES,
        widget=django_filters.widgets.CSVWidget,
    )
    priority = django_filters.MultipleChoiceFilter(
        choices=Lead.PRIORITIES,
        widget=django_filters.widgets.CSVWidget,
    )
    assignee = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
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
        choices=EXISTS_CHOICE, method='exists_filter',
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
        choices=FILTERED_ENTRIES_CHOICE, method='filtered_exists_filter',
    )

    class Meta:
        model = Lead
        fields = {
            **{
                x: ['exact']
                for x in ['id', 'title', 'text', 'url', 'website']
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
        if value == self.ENTRIES_EXIST:
            return qs.filter(entry__isnull=False)
        elif value == self.ASSESSMENT_EXISTS:
            return qs.filter(assessment__isnull=False)
        elif value == self.ENTRIES_DO_NOT_EXIST:
            return qs.filter(entry__isnull=True)
        elif value == self.ASSESSMENT_DOES_NOT_EXIST:
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
            return qs.filter(organization_types__in=[ot.id for ot in value]).distinct()
        return qs

    def filtered_exists_filter(self, qs, name, value):
        # NOTE: check annotations at Lead.get_for
        if value == self.EXCLUDE_EMPTY_FILTERED_ENTRIES:
            return qs.filter(filtered_entries_count__gte=1)
        elif value == self.EXCLUDE_EMPTY_VERIFIED_FILTERED_ENTRIES:
            return qs.filter(verified_filtered_entries_count__gte=1)
        return qs


class LeadGQFilterSet(LeadFilterSet):
    ordering = None

    @property
    def qs(self):
        return super().qs.distinct()


class LeadGroupFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
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
