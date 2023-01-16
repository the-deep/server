from django.db import models
import django_filters

from deep.filter_set import OrderEnumMixin, generate_type_for_filter_set
from utils.graphene.filters import IDListFilter
from user_resource.filters import UserResourceGqlFilterSet

from .models import Project
from entry.models import Entry


class ExploreProjectFilterSet(OrderEnumMixin, UserResourceGqlFilterSet):
    organizations = IDListFilter(distinct=True)
    is_test = django_filters.BooleanFilter(method='filter_is_test')
    search = django_filters.CharFilter(method='filter_title')
    exclude_entry_less_than = django_filters.BooleanFilter(method='filter_exclude_entry_less_than')
    regions = IDListFilter(distinct=True)

    class Meta:
        model = Project
        fields = ()

    def filter_is_test(self, qs, _, value):
        if value is None:
            return qs
        return qs.filter(is_test=value)

    def filter_title(self, qs, _, value):
        if not value:
            return qs
        return qs.filter(title__icontains=value)

    def filter_exclude_entry_less_than(self, qs, _, value):
        if value is True:
            return qs.annotate(
                entry_count=models.functions.Coalesce(models.Subquery(
                    Entry.objects.filter(
                        project=models.OuterRef('id')
                    ).order_by().values('project').annotate(
                        count=models.Count('id', distinct=True)
                    ).values('count')[:1],
                    output_field=models.IntegerField()
                ), 0)
            ).filter(entry_count__gt=100)
        # False and None has same result
        return qs

    @property
    def qs(self):
        return super().qs.distinct()


ExploreProjectFilterDataType, ExploreProjectFilterDataInputType = generate_type_for_filter_set(
    ExploreProjectFilterSet,
    'project.schema.ProjectListType',
    'ExploreProjectFilterDataType',
    'ExploreProjectFilterDataInputType',
)
