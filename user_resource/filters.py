from django.contrib.auth.models import User
import django_filters


class UserResourceFilterSet(django_filters.FilterSet):
    created_at = django_filters.DateTimeFromToRangeFilter()
    modified_at = django_filters.DateTimeFromToRangeFilter()
    created_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all())
    modified_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all())
