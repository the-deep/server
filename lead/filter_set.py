from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
from project.models import Project
from user.models import User
from .models import Lead, LeadGroup


class LeadFilterSet(UserResourceFilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """
    published_on__lt = django_filters.DateFilter(
        name='published_on', lookup_expr='lte',
    )
    published_on__gt = django_filters.DateFilter(
        name='published_on', lookup_expr='gte',
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

    class Meta:
        model = Lead
        fields = ['id', 'title',
                  'text', 'url', 'website']

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
