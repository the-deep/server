import django_filters
from django.db import models
from django.db.models.functions import Coalesce
from entry.filter_set import EntryGQFilterSet
from user_resource.filters import UserResourceGqlFilterSet

from utils.graphene.filters import IDListFilter, MultipleInputFilter

from .enums import AnalysisReportUploadTypeEnum, DiscardedEntryTagTypeEnum
from .models import (
    Analysis,
    AnalysisPillar,
    AnalysisReport,
    AnalysisReportSnapshot,
    AnalysisReportUpload,
    AnalyticalStatement,
    DiscardedEntry,
)


class AnalysisFilterSet(django_filters.FilterSet):
    created_at__lt = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lt",
        input_formats=["%Y-%m-%d%z"],
    )
    created_at__gt = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gt",
        input_formats=["%Y-%m-%d%z"],
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        input_formats=["%Y-%m-%d%z"],
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        input_formats=["%Y-%m-%d%z"],
    )
    created_at = django_filters.DateTimeFilter(
        field_name="created_at",
        input_formats=["%Y-%m-%d%z"],
    )

    class Meta:
        model = Analysis
        fields = ()


class DiscardedEntryFilterSet(django_filters.FilterSet):
    tag = django_filters.MultipleChoiceFilter(
        choices=DiscardedEntry.TagType.choices,
        lookup_expr="in",
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = DiscardedEntry
        fields = []


# -------------------- Graphql Filters -----------------------------------
class AnalysisGQFilterSet(UserResourceGqlFilterSet):
    class Meta:
        model = Analysis
        fields = ()


class AnalysisPillarGQFilterSet(UserResourceGqlFilterSet):
    analyses = IDListFilter(field_name="analysis")

    class Meta:
        model = AnalysisPillar
        fields = ()


class AnalysisPillarEntryGQFilterSet(EntryGQFilterSet):
    discarded = django_filters.BooleanFilter(method="filter_discarded")
    exclude_entries = IDListFilter(method="filter_exclude_entries")

    def filter_discarded(self, queryset, *_):
        # NOTE: This is only for argument, filter is done in AnalysisPillarType.resolve_entries
        return queryset

    def filter_exclude_entries(self, queryset, _, value):
        if value:
            return queryset.exclude(id__in=value)
        return queryset


class AnalyticalStatementGQFilterSet(UserResourceGqlFilterSet):
    class Meta:
        model = AnalyticalStatement
        fields = ()


class AnalysisPillarDiscardedEntryGqlFilterSet(django_filters.FilterSet):
    tags = MultipleInputFilter(DiscardedEntryTagTypeEnum, field_name="tag")

    class Meta:
        model = DiscardedEntry
        fields = []


class AnalysisReportGQFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method="search_filter")
    analyses = IDListFilter(field_name="analysis")
    is_public = django_filters.BooleanFilter(method="filter_discarded")
    organizations = IDListFilter(method="organizations_filter")

    class Meta:
        model = AnalysisReport
        fields = []

    def organizations_filter(self, qs, _, value):
        if value:
            qs = (
                qs.annotate(authoring_organizations=Coalesce("authors__parent_id", "authors__id"))
                .filter(authoring_organizations__in=value)
                .distinct()
            )
        return qs

    def search_filter(self, qs, _, value):
        if value:
            qs = qs.filter(models.Q(slug__icontains=value) | models.Q(title__icontains=value)).distinct()
        return qs


class AnalysisReportUploadGQFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method="search_filter")
    report = IDListFilter(field_name="report")
    types = MultipleInputFilter(AnalysisReportUploadTypeEnum, field_name="type")

    class Meta:
        model = AnalysisReportUpload
        fields = []

    def search_filter(self, qs, _, value):
        if value:
            qs = qs.filter(models.Q(file__title__icontains=value)).distinct()
        return qs


class AnalysisReportSnapshotGQFilterSet(django_filters.FilterSet):
    report = IDListFilter(field_name="report")

    class Meta:
        model = AnalysisReportSnapshot
        fields = []
