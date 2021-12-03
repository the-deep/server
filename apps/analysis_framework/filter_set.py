from django.db import models
import django_filters

from user_resource.filters import (
    UserResourceFilterSet,
    UserResourceGqlFilterSet,
)
from .models import (
    AnalysisFramework,
)


class AnalysisFrameworkFilterSet(UserResourceFilterSet):
    class Meta:
        model = AnalysisFramework
        fields = ('id', 'title', 'description', 'created_at',)

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda _: {
                    'lookup_expr': 'icontains',
                },
            },
        }


# ----------------------------- Graphql Filters ---------------------------------------
class AnalysisFrameworkGqFilterSet(UserResourceGqlFilterSet):
    search = django_filters.CharFilter(method='search_filter')
    is_current_user_member = django_filters.BooleanFilter(
        field_name='is_current_user_member', method='filter_with_membership')

    class Meta:
        model = AnalysisFramework
        fields = ['id']

    def search_filter(self, qs, _, value):
        if value:
            return qs.filter(models.Q(title__icontains=value))
        return qs

    def filter_with_membership(self, queryset, _, value):
        if value is not None:
            filter_query = models.Q(members=self.request.user)
            afs = AnalysisFramework.objects.all()
            if value:
                afs = afs.filter(filter_query)
            else:
                afs = afs.exclude(filter_query)
            return queryset.filter(id__in=afs)
        return queryset
