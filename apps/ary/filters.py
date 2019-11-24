import django_filters
from django.db import models

from user_resource.filters import UserResourceFilterSet
from user.models import User
from project.models import Project
from lead.models import Lead, LeadGroup

from .models import (
    Assessment,
    PlannedAssessment,
)


class AssessmentFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        field_name='lead__project',
        lookup_expr='in',
    )
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
    )
    lead_group = django_filters.ModelMultipleChoiceFilter(
        queryset=LeadGroup.objects.all(),
        lookup_expr='in',
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = Assessment
        fields = ['id', 'lead__title', 'lead_group__title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class PlannedAssessmentFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        field_name='project',
        lookup_expr='in',
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = PlannedAssessment
        fields = ['id', 'title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
