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
