import django_filters
from django.db import models

from utils.db.functions import StrPos
from utils.graphene.filters import IDFilter

from .models import UserGroup


class UserGroupFilterSet(django_filters.FilterSet):
    is_current_user_member = django_filters.BooleanFilter(field_name="is_current_user_member", method="filter_with_membership")

    class Meta:
        model = UserGroup
        fields = ["id"]

    def filter_with_membership(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(
                id__in=UserGroup.get_for_member(
                    self.request.user,
                    exclude=not value,
                )
            )
        return queryset


class UserGroupGQFilterSet(UserGroupFilterSet):
    search = django_filters.CharFilter(method="filter_search")
    members_include_project = IDFilter(method="filter_include_project")
    members_exclude_project = IDFilter(method="filter_exclude_project")

    class Meta:
        model = UserGroup
        fields = ()

    def filter_search(self, qs, name, value):
        if value:
            return (
                qs.annotate(strpos=StrPos(models.functions.Lower("title"), models.Value(value.lower(), models.CharField())))
                .filter(strpos__gte=1)
                .order_by("strpos")
            )
        return qs

    def filter_exclude_project(self, qs, name, value):
        if value:
            qs = qs.filter(~models.Q(projectusergroupmembership__project_id=value)).distinct()
        return qs

    def filter_include_project(self, qs, name, value):
        if value:
            qs = qs.filter(projectusergroupmembership__project_id=value).distinct()
        return qs
