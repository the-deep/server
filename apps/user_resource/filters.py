from django.contrib.auth.models import User
import django_filters


class UserResourceFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d%z']
    )
    created_at__gt = django_filters.DateFilter(
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
