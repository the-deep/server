from django.contrib.auth.models import User
import django_filters


class UserResourceFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateFilter(
        name='created_at', lookup_expr='lte',
    )
    created_at__gt = django_filters.DateFilter(
        name='created_at', lookup_expr='gte',
    )
    modified_at__lt = django_filters.DateFilter(
        name='modified_at', lookup_expr='lte',
    )
    modified_at__gt = django_filters.DateFilter(
        name='modified_at', lookup_expr='gte',
    )
    created_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all())
    modified_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all())
