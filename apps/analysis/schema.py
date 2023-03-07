import graphene

from django.db import models
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from user_resource.schema import UserResourceMixin, resolve_user_field

from lead.models import Lead
from entry.models import Entry
from entry.schema import get_entry_qs
from user.schema import UserType

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
)
# from .enums import DiscardedEntryTagTypeEnum
from .filter_set import (
    AnalysisGQFilterSet,
    AnalysisPillarGQFilterSet,
    AnalysisPillarEntryGQFilterSet,
    AnalyticalStatementGQFilterSet,
)


def _get_qs(model, info):
    qs = model.objects.filter(
        # Filter by project
        project=info.context.active_project,
    )
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return qs
    return qs.objects.none()


def get_analysis_qs(info):
    return _get_qs(Analysis, info)


def get_analysis_pillar_qs(info):
    return _get_qs(AnalysisPillar, info)


def get_analytical_statement_qs(info):
    return _get_qs(AnalyticalStatement, info)


class AnalyticalStatementEntryType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatementEntry
        only_fields = (
            'id',
            'order',
        )

    entry = graphene.ID(source='entry_id', required=True)
    analytical_statement = graphene.ID(source='analytical_statement_id', required=True)


class AnalyticalStatementType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatement
        only_fields = (
            'id',
            'statement',
            'include_in_report',
            'order',
        )

    cloned_from = graphene.ID(source='cloned_from_id')
    entries_count = graphene.Int(required=True)

    # XXX: N+1 and No pagination
    entries = graphene.List(graphene.NonNull(AnalyticalStatementEntryType))

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analytical_statement_qs(info)

    @staticmethod
    def resolve_entries_count(root, info, **_):
        return info.context.dl.analysis.analysis_statement_analyzed_entries.load(root.id)

    @staticmethod
    def resolve_entries(root, info, **_):
        return info.context.dl.analysis.analytical_statement_entries.load(root.id)


class AnalysisPillarEntryListType(CustomDjangoListObjectType):
    class Meta:
        model = Entry
        filterset_class = AnalysisPillarEntryGQFilterSet


class AnalysisPillarType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisPillar
        only_fields = (
            'id',
            'title',
            'main_statement',
            'information_gap',
            'filters',
        )

    assignee = graphene.Field(UserType, required=True)
    analysis = graphene.ID(source='analysis_id', required=True)
    cloned_from = graphene.ID(source='cloned_from_id')
    analyzed_entries_count = graphene.Int(required=True)

    # XXX: N+1 and No pagination
    statements = graphene.List(graphene.NonNull(AnalyticalStatementType))

    entries = DjangoPaginatedListObjectField(
        AnalysisPillarEntryListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analysis_pillar_qs(info)

    @staticmethod
    def resolve_assignee(root, info, **_):
        return resolve_user_field(root, info, 'assignee')

    @staticmethod
    def resolve_analyzed_entries_count(root, info, **_):
        return info.context.dl.analysis.analysis_pillars_analyzed_entries.load(root.id)

    @staticmethod
    def resolve_statements(root, info, **_):
        return info.context.dl.analysis.analysis_pillar_analytical_statements.load(root.id)

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


class AnalysisType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = Analysis
        only_fields = (
            'id',
            'title',
            'start_date',
            'end_date',
        )

    cloned_from = graphene.ID(source='cloned_from_id')
    team_lead = graphene.Field(UserType, required=True)
    publication_date = graphene.Field(
        type('AnalysisPublicationDateType', (graphene.ObjectType,), {
            'start_date': graphene.Date(required=True),
            'end_date': graphene.Date(required=True),
        })
    )
    analyzed_entries_count = graphene.Int(required=True)
    analyzed_leads_count = graphene.Int(required=True)

    # XXX: N+1 and No pagination
    pillars = graphene.List(graphene.NonNull(AnalysisPillarType))

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analysis_qs(info)

    @staticmethod
    def resolve_team_lead(root, info, **_):
        return resolve_user_field(root, info, 'team_lead')

    @staticmethod
    def resolve_publication_date(root, info, **_):
        return info.context.dl.analysis.analysis_publication_date.load(root.id)

    @staticmethod
    def resolve_analyzed_entries_count(root, info, **_):
        return info.context.dl.analysis.analysis_analyzed_entries.load(root.id)

    @staticmethod
    def resolve_analyzed_leads_count(root, info, **_):
        return info.context.dl.analysis.analysis_analyzed_leads.load(root.id)

    @staticmethod
    def resolve_pillars(root, info, **_):
        return info.context.dl.analysis.analysis_analysis_pillars.load(root.id)


class AnalysisOverviewType(graphene.ObjectType):
    total_entries_count = graphene.Int(required=True)
    total_leads_count = graphene.Int(required=True)
    analyzed_entries_count = graphene.Int(required=True)
    analyzed_leads_count = graphene.Int(required=True)

    authoring_organizations = graphene.List(graphene.NonNull(
        type('AnalysisOverviewOrganizationType', (graphene.ObjectType,), {
            'id': graphene.ID(required=True),
            'title': graphene.String(required=True),
            'count': graphene.Int(required=True),
        })
    ))
    # analysis_list': analysis_list,
    # analysis_list = Analysis.objects.filter(project=project_id).values('id', 'title', 'created_at')

    @staticmethod
    def resolve_total_entries_count(root, info, **_):
        return Entry.objects.filter(project=info.context.active_project).count()

    @staticmethod
    def resolve_total_leads_count(root, info, **_):
        return Lead.objects\
            .filter(project=info.context.active_project)\
            .annotate(entries_count=models.Count('entry'))\
            .filter(entries_count__gt=0)\
            .count()

    @staticmethod
    def resolve_analyzed_entries_count(root, info, **_):
        project = info.context.active_project
        entries_dragged = AnalyticalStatementEntry.objects\
            .filter(analytical_statement__analysis_pillar__analysis__project=project)\
            .order_by().values('entry').distinct()
        entries_discarded = DiscardedEntry.objects\
            .filter(analysis_pillar__analysis__project=project)\
            .order_by().values('entry').distinct()
        return entries_discarded.union(entries_dragged).count()

    @staticmethod
    def resolve_analyzed_leads_count(root, info, **_):
        project = info.context.active_project
        sources_discarded = DiscardedEntry.objects\
            .filter(analysis_pillar__analysis__project=project)\
            .order_by().values('entry__lead_id').distinct()
        sources_dragged = AnalyticalStatementEntry.objects\
            .filter(analytical_statement__analysis_pillar__analysis__project=project)\
            .order_by().values('entry__lead_id').distinct()
        return sources_dragged.union(sources_discarded).count()

    @staticmethod
    def resolve_authoring_organizations(root, info, **_):
        lead_qs = Lead.objects\
            .filter(
                project=info.context.active_project,
                authors__organization_type__isnull=False,
            )\
            .annotate(
                entries_count=models.functions.Coalesce(models.Subquery(
                    AnalyticalStatementEntry.objects.filter(
                        entry__lead_id=models.OuterRef('pk')
                    ).order_by().values('entry__lead_id').annotate(count=models.Count('*'))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0)
            ).filter(entries_count__gt=0)
        qs = Lead.objects\
            .filter(id__in=lead_qs)\
            .order_by('authors__organization_type').values('authors__organization_type')\
            .annotate(
                count=models.Count('id'),
                organization_type_title=models.functions.Coalesce(
                    models.F('authors__organization_type__title'),
                    models.Value(''),
                )
            ).values_list(
                'count',
                'organization_type_title',
                models.F('authors__organization_type__id')
            )
        return [
            dict(
                id=_id,
                title=title,
                count=count,
            )
            for count, title, _id in qs
        ]


class AnalysisPillarListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisPillar
        filterset_class = AnalysisPillarGQFilterSet


class AnalysisListType(CustomDjangoListObjectType):
    class Meta:
        model = Analysis
        filterset_class = AnalysisGQFilterSet


class AnalyticalStatementListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalyticalStatement
        filterset_class = AnalyticalStatementGQFilterSet


class Query:
    analysis_overview = graphene.Field(AnalysisOverviewType)
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

    # Statement
    analytical_statement = DjangoObjectField(AnalyticalStatementType)
    analytical_statements = DjangoPaginatedListObjectField(
        AnalyticalStatementListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_analysis_overview(*_):
        return {}

    @staticmethod
    def resolve_analyses(root, info, **kwargs) -> models.QuerySet:
        return get_analysis_qs(info)

    @staticmethod
    def resolve_analysis_pillars(root, info, **kwargs) -> models.QuerySet:
        return get_analysis_pillar_qs(info)

    @staticmethod
    def resolve_analytical_statements(root, info, **kwargs) -> models.QuerySet:
        return get_analytical_statement_qs(info)
