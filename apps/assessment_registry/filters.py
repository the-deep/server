import django_filters
from django.db import models
from django.db.models import Q

from user_resource.filters import UserResourceGqlFilterSet
from utils.graphene.filters import SimpleInputFilter

from user.models import User
from project.models import Project
from lead.models import Lead

from .models import AssessmentRegistry, SummaryIssue
from .enums import AssessmentRegistrySummarySubPillarTypeEnum, AssessmentRegistrySummarySubDimmensionTypeEnum


class AssessmentRegistryGQFilterSet(UserResourceGqlFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        field_name='lead__project',
    )
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=django_filters.widgets.CSVWidget,
    )
    publication_date_lte = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z']
    )
    publication_date_gte = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d%z']
    )
    search = django_filters.CharFilter(method='filter_assessment_registry')

    class Meta:
        model = AssessmentRegistry
        fields = ()

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    def filter_assessment_registry(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            Q(id=value) |
            Q(lead__title__icontains=value)
        ).distinct()


class IssueGQFilterSet(django_filters.FilterSet):
    sub_pillar = SimpleInputFilter(AssessmentRegistrySummarySubPillarTypeEnum)
    sub_dimmension = SimpleInputFilter(AssessmentRegistrySummarySubDimmensionTypeEnum)

    class Meta:
        model = SummaryIssue
        fields = ('label', 'parent',)
