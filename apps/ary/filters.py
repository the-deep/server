import django_filters
from django.db import models

from user_resource.filters import UserResourceFilterSet
from user.models import User
from project.models import Project
from lead.models import Lead, LeadGroup
from user_resource.filters import UserResourceGqlFilterSet

from .models import (
    Assessment,
    PlannedAssessment,
)


class AssessmentFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        field_name='lead__project',
    )
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
    )
    lead_group = django_filters.ModelMultipleChoiceFilter(
        queryset=LeadGroup.objects.all(),
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
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
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
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


# -------------------- Graphql Filters -----------------------------------
class AssessmentGQFilterSet(UserResourceGqlFilterSet):
    search = django_filters.CharFilter(method='filter_title')

    class Meta:
        model = Assessment
        fields = ()

    def filter_title(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            models.Q(lead__title__icontains=value) |
            models.Q(lead_group__title__icontains=value)
        ).distinct()
