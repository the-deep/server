from django.db import models
from django.db.models.functions import Concat, Lower
import django_filters

from utils.graphene.filters import SimpleInputFilter, IDListFilter
from user_resource.filters import UserResourceFilterSet, UserResourceGqlFilterSet

from .models import (
    Project,
    ProjectMembership,
    ProjectUserGroupMembership,
)
from .enums import (
    ProjectStatusEnum,
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

    is_current_user_member = django_filters.BooleanFilter(
        field_name='is_current_user_member', method='filter_with_membership')

    def filter_with_membership(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(
                id__in=Project.get_for_member(
                    self.request.user,
                    exclude=not value,
                )
            )
        return queryset


class ProjectMembershipFilterSet(UserResourceFilterSet):
    class Meta:
        model = ProjectMembership
        fields = ['id', 'project', 'member']


class ProjectUserGroupMembershipFilterSet(UserResourceFilterSet):
    class Meta:
        model = ProjectUserGroupMembership
        fields = ['id', 'project', 'usergroup']


def get_filtered_projects(user, queries, annotate=False):
    projects = Project.get_for(user, annotate)
    involvement = queries.get('involvement')
    if involvement:
        if involvement == 'my_projects':
            projects = projects.filter(Project.get_query_for_member(user))
        if involvement == 'not_my_projects':
            projects = projects.exclude(Project.get_query_for_member(user))

    regions = queries.get('regions') or ''
    if regions:
        projects = projects.filter(regions__in=regions.split(','))

    ordering = queries.get('ordering')
    if ordering:
        projects = projects.order_by(ordering)

    return projects.distinct()


# -------------------- Graphql Filters -----------------------------------
class ProjectGqlFilterSet(UserResourceGqlFilterSet):
    ids = IDListFilter(field_name='id')
    status = SimpleInputFilter(ProjectStatusEnum)
    organizations = IDListFilter(distinct=True)
    analysis_frameworks = IDListFilter(field_name='analysis_framework')
    regions = IDListFilter(distinct=True)
    search = django_filters.CharFilter(method='filter_title')
    is_current_user_member = django_filters.BooleanFilter(
        field_name='is_current_user_member', method='filter_with_membership')

    class Meta:
        model = Project
        fields = ()

    def filter_title(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(title__icontains=value).distinct()

    def filter_with_membership(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(
                id__in=Project.get_for_member(
                    self.request.user,
                    exclude=not value,
                )
            )
        return queryset


class ProjectMembershipGqlFilterSet(UserResourceGqlFilterSet):
    search = django_filters.CharFilter(method='filter_search')
    members = IDListFilter(distinct=True, field_name='member')

    class Meta:
        model = ProjectMembership
        fields = ('id',)

    def filter_search(self, qs, _, value):
        if value:
            return qs.annotate(
                full_name=Lower(
                    Concat(
                        'member__first_name', models.Value(' '), 'member__last_name', models.Value(' '), 'member__email',
                        output_field=models.CharField(),
                    )
                ),
            ).filter(full_name__icontains=value).distinct()
        return qs


class ProjectUserGroupMembershipGqlFilterSet(UserResourceGqlFilterSet):
    search = django_filters.CharFilter(method='filter_search')
    usergroups = IDListFilter(distinct=True, field_name='usergroup')

    class Meta:
        model = ProjectUserGroupMembership
        fields = ('id',)

    def filter_search(self, qs, _, value):
        if value:
            return qs.filter(usergroup__title__icontains=value).distinct()
        return qs
