from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
from .models import Project


class ProjectFilterSet(UserResourceFilterSet):
    # TODO: `status` filter based on project activity

    class Meta:
        model = Project
        fields = ['id', 'title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
