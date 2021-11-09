from utils.graphene.filters import IDListFilter
from django.contrib.auth.models import User
import django_filters


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
    created_at_gte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601]
    )
    created_at_lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601]
    )
    modified_at_gte = django_filters.DateTimeFilter(
        field_name='modified_at',
        lookup_expr='gte',
        input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601]
    )
    modified_at_lte = django_filters.DateTimeFilter(
        field_name='modified_at',
        lookup_expr='lte',
        input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601]
    )
    created_by = IDListFilter()
    modified_by = IDListFilter()
