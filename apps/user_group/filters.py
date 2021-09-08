import django_filters

from .models import (
    UserGroup,
)


class UserGroupFilterSet(django_filters.FilterSet):
    is_current_user_member = django_filters.BooleanFilter(
        field_name='is_current_user_member', method='filter_with_membership')

    class Meta:
        model = UserGroup
        fields = ['id']

    def filter_with_membership(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(
                id__in=UserGroup.get_for_member(
                    self.request.user,
                    exclude=not value,
                )
            )
        return queryset
