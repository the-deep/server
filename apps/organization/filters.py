import django_filters

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db import models

from .models import Organization


class IsFromReliefWeb(admin.SimpleListFilter):
    YES = 'yes'
    NO = 'no'

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Is from Relief Web')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_from_relief_web'

    def lookups(self, request, model_admin):
        return (
            (self.YES, 'Yes'),
            (self.NO, 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == self.YES:
            return queryset.filter(relief_web_id__isnull=False)
        if self.value() == self.NO:
            return queryset.filter(relief_web_id__isnull=True)
        else:
            return queryset.all()


class OrganizationFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Organization
        fields = ['id']

    def search_filter(self, qs, _, value):
        if value:
            return qs.filter(
                models.Q(title__icontains=value) |
                models.Q(short_name__icontains=value) |
                models.Q(long_name__icontains=value)
            ).distinct()
        return qs
