from django.db import models
import django_filters

from user_resource.filters import (
    UserResourceFilterSet,
    UserResourceGqlFilterSet,
)
from .models import (
    AnalysisFramework,
)
from entry.models import Entry
from django.utils import timezone
from datetime import timedelta


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
    recently_used = django_filters.BooleanFilter(
        method='filter_recently_used',
        label='Recently Used',
    )

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

    def filter_recently_used(self, queryset, name, value):
        if value:
            # Calculate the date for "recent" usage (e.g., within the last 6 months or 180 days)
            recent_usage_cutoff = timezone.now() - timedelta(days=180)
            entries_qs = Entry.objects.filter(modified_at__gte=recent_usage_cutoff)
            return queryset.filter(id__in=entries_qs.values('analysis_framework'))
        return queryset
