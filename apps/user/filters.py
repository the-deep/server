import django_filters
from django.db import models
from django.db.models.functions import Concat
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
            qs = qs.annotate(
                full_name=Concat(
                    models.F("first_name"),
                    models.Value(" "),
                    models.F("last_name"),
                    output_field=models.CharField(),
                )
            ).filter(
                models.Q(full_name__unaccent__icontains=value) |
                models.Q(first_name__unaccent__icontains=value) |
                models.Q(last_name__unaccent__icontains=value) |
                models.Q(email__unaccent__icontains=value) |
                models.Q(username__unaccent__icontains=value)
            )
        return qs

    @property
    def qs(self):
        # Filter out deleted users
        return super().qs.filter(profile__deleted_at__isnull=True)
