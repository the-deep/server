import django_filters
from django.contrib.auth.models import User

from utils.graphene.filters import (
    IDListFilter,
    DateTimeFilter,
    DateTimeGteFilter,
    DateTimeLteFilter,
)


class UserResourceFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z']
    )
    created_at__gte = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d%z']
    )
    modified_at__lt = django_filters.DateFilter(
        field_name='modified_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z']
    )
    modified_at__gt = django_filters.DateFilter(
        field_name='modified_at',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d%z']
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all())
    modified_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all())


class UserResourceGqlFilterSet(django_filters.FilterSet):
    created_at = DateTimeFilter()
    created_at_gte = DateTimeGteFilter(field_name='created_at')
    created_at_lte = DateTimeLteFilter(field_name='created_at')
    modified_at = DateTimeFilter()
    modified_at_gte = DateTimeGteFilter(field_name='modified_at')
    modified_at_lte = DateTimeLteFilter(field_name='modified_at')
    created_by = IDListFilter()
    modified_by = IDListFilter()
