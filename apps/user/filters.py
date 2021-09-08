import django_filters

from .models import User


class UserFilterSet(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ['id']
