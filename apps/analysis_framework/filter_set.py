from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
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


class AnalysisFrameworkGqFilterSet(UserResourceFilterSet):
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = AnalysisFramework
        fields = ['id']

    def search_filter(self, qs, _, value):
        if value:
            return qs.filter(models.Q(title__icontains=value)).distinct()
        return qs
