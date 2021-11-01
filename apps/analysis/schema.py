import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP

from entry.models import Entry
from entry.schema import get_entry_qs

from .models import (
    Analysis,
    AnalysisPillar,
    DiscardedEntry,
)
# from .enums import DiscardedEntryTagTypeEnum
from .filter_set import (
    AnalysisGQFilterSet,
    AnalysisPillarGQFilterSet,
    AnalysisPillarEntryGQFilterSet,
)


def get_analysis_qs(info):
    analysis_qs = Analysis.objects.filter(
        # Filter by project
        project=info.context.active_project,
    )
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return analysis_qs
    return Analysis.objects.none()


def get_analysis_pillar_qs(info):
    pillar_qs = AnalysisPillar.objects.filter(
        # Filter by project
        analysis__project=info.context.active_project,
    )
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return pillar_qs
    return AnalysisPillar.objects.none()


class AnalysisType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Analysis
        fields = (
            'id',
            'title', 'start_date', 'end_date',
        )

    team_lead = graphene.ID(source='team_lead_id', required=True)
    cloned_from = graphene.ID(source='cloned_from_id', required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_analysis_qs(info)


class AnalysisListType(CustomDjangoListObjectType):
    class Meta:
        model = Analysis
        filterset_class = AnalysisGQFilterSet


class AnalysisPillarEntryListType(CustomDjangoListObjectType):
    class Meta:
        model = Entry
        filterset_class = AnalysisPillarEntryGQFilterSet


class AnalysisPillarType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisPillar
        fields = (
            'id',
            'title', 'main_statement', 'information_gap', 'assignee',
            'filters',
        )

    analysis = graphene.ID(source='analysis_id', required=True)
    cloned_from = graphene.ID(source='cloned_from_id', required=True)

    entries = DjangoPaginatedListObjectField(
        AnalysisPillarEntryListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_analysis_pillar_qs(info)

    @staticmethod
    def resolve_entries(root, info, **kwargs):
        # filtering out the entries whose lead published_on date is less than analysis end_date
        queryset = get_entry_qs(info).filter(
            project=root.analysis.project_id,
            lead__published_on__lte=root.analysis.end_date
        )
        discarded_entries_qs = DiscardedEntry.objects.filter(analysis_pillar=root).values('entry')
        if kwargs.get('discarded'):  # NOTE: From AnalysisPillarEntryGQFilterSet.discarded
            return queryset.filter(id__in=discarded_entries_qs)
        return queryset.exclude(id__in=discarded_entries_qs)


class AnalysisPillarListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisPillar
        filterset_class = AnalysisPillarGQFilterSet


class Query:
    analysis = DjangoObjectField(AnalysisType)
    analyses = DjangoPaginatedListObjectField(
        AnalysisListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    # Pillar
    analysis_pillar = DjangoObjectField(AnalysisPillarType)
    analysis_pillars = DjangoPaginatedListObjectField(
        AnalysisPillarListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_analyses(root, info, **kwargs) -> QuerySet:
        return get_analysis_qs(info)

    @staticmethod
    def resolve_pillars(root, info, **kwargs) -> QuerySet:
        return get_analysis_pillar_qs(info).filter(analysis=root)
