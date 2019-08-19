from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
from project.models import Project
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
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    confidentiality = django_filters.MultipleChoiceFilter(
        choices=Lead.CONFIDENTIALITIES,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Lead.STATUSES,
        lookup_expr='in',
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

    class Meta:
        model = Lead
        fields = {
            **{
                x: ['exact']
                for x in ['id', 'title', 'text', 'url', 'website']
            },
            'created_at': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'published_on': ['exact', 'lt', 'gt', 'lte', 'gte']
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


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
