import django_filters
from django.db import models

from utils.graphene.filters import IDFilter

from .models import User


class UserFilterSet(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ['id']


# -------------------- Graphql Filter ---------------------------------
class UserGqlFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    members_exclude_project = IDFilter(method='filter_exclude_project')
    members_exclude_framework = IDFilter(method='filter_exclude_framework')
    members_exclude_usergroup = IDFilter(method='filter_exclude_usergroup')

    class Meta:
        model = User
        fields = ('id',)

    def filter_exclude_project(self, qs, name, value):
        if value:
            qs = qs.filter(
                ~models.Q(projectmembership__project_id=value)
            ).distinct()
        return qs

    def filter_exclude_framework(self, qs, name, value):
        if value:
            qs = qs.filter(
                ~models.Q(framework_membership__framework_id=value)
            )
        return qs

    def filter_exclude_usergroup(self, qs, name, value):
        if value:
            qs = qs.filter(
                ~models.Q(groupmembership__group_id=value)
            )
        return qs
    
    def filter_search(self, qs, name, value):
        if value:
            first_name, last_name = value.split(' ', 1) if ' ' in value else (value, '')
        
        if first_name and last_name:
            qs = qs.filter(
                models.Q(first_name__icontains=first_name) &
                models.Q(last_name__icontains=last_name)
            )
        else:
            qs = qs.filter(
                models.Q(first_name__icontains=value) |
                models.Q(last_name__icontains=value) |
                models.Q(email__icontains=value) |
                models.Q(username__icontains=value)
            )

        return qs

    @property
    def qs(self):
        # Filter out deleted users
        return super().qs.filter(profile__deleted_at__isnull=True)
