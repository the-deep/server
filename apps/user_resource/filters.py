from django.contrib.auth.models import User
import django_filters


class UserResourceFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__lt',
    )
    created_at__gt = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__gt',
    )
    created_at__lte = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__lte',
    )
    created_at__gte = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__gte',
    )

    modified_at__lt = django_filters.DateFilter(
        field_name='modified_at', lookup_expr='date__lt',
    )
    modified_at__gt = django_filters.DateFilter(
        field_name='modified_at', lookup_expr='date__gt',
    )
    modified_at__lte = django_filters.DateFilter(
        field_name='modified_at', lookup_expr='date__lte',
    )
    modified_at__gte = django_filters.DateFilter(
        field_name='modified_at', lookup_expr='date__gte',
    )

    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all())
    modified_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all())
