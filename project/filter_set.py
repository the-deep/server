from django.db import models
import django_filters

from user_resource.filters import UserResourceFilterSet
from .models import (
    Project,
    ProjectMembership,
    ProjectUserGroupMembership,
)


class ProjectFilterSet(UserResourceFilterSet):
    class Meta:
        model = Project
        fields = ['id', 'title', 'status', 'user_groups']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class ProjectMembershipFilterSet(UserResourceFilterSet):
    class Meta:
        model = ProjectMembership
        fields = ['id', 'project', 'member']


class ProjectUserGroupMembershipFilterSet(UserResourceFilterSet):
    class Meta:
        model = ProjectUserGroupMembership
        fields = ['id', 'project', 'usergroup']


def get_filtered_projects(user, queries):
    projects = Project.get_for(user)
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
