from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
from .models import Project, ProjectStatus


class ProjectFilterSet(UserResourceFilterSet):
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


def get_filtered_projects(user, queries):
    projects = Project.get_for(user)

    status = queries.get('status')
    if status:
        statuses = list(ProjectStatus.objects.filter(
            id__in=status.split(',')
        ))

        query = statuses.pop().get_query()
        for status in statuses:
            query |= status.get_query()

        projects = projects.filter(query)

    involvement = queries.get('involvement')
    if involvement:
        if involvement == 'my_projects':
            projects = projects.filter(Project.get_query_for_member(user))
        if involvement == 'not_my_projects':
            projects = projects.exclude(Project.get_query_for_member(user))

    ordering = queries.get('ordering')
    if ordering:
        projects = projects.order_by(ordering)

    return projects.distinct()
