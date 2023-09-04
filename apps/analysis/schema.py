import graphene

from django.db import models
from django.db.models.functions import Cast
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin, FileFieldType
from utils.graphene.fields import DjangoPaginatedListObjectField, generate_type_for_serializer
from utils.graphene.enums import EnumDescription
from utils.graphene.geo_scalars import PointScalar
from utils.common import has_select_related
from utils.db.functions import IsEmpty
from deep.permissions import ProjectPermissions as PP
from user_resource.schema import UserResourceMixin, resolve_user_field

from lead.models import Lead
from analysis_framework.models import Widget
from geo.models import GeoArea
from entry.models import Entry, Attribute
from entry.schema import get_entry_qs, EntryType
from entry.filter_set import EntriesFilterDataType
from user.schema import UserType
from organization.schema import OrganizationType

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
    TopicModel,
    TopicModelCluster,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
    AnalyticalStatementGeoEntry,
    AnalysisReport,
    AnalysisReportUpload,
    AnalysisReportContainer,
    AnalysisReportContainerData,
    AnalysisReportSnapshot,
)
from .enums import (
    DiscardedEntryTagTypeEnum,
    TopicModelStatusEnum,
    AutomaticSummaryStatusEnum,
    AnalyticalStatementNGramStatusEnum,
    AnalysisReportContainerContentTypeEnum,
    AnalyticalStatementGeoTaskStatusEnum,
    AnalysisReportUploadTypeEnum,
)
from .filter_set import (
    AnalysisGQFilterSet,
    AnalysisPillarGQFilterSet,
    AnalysisPillarEntryGQFilterSet,
    AnalyticalStatementGQFilterSet,
    AnalysisPillarDiscardedEntryGqlFilterSet,
    AnalysisReportGQFilterSet,
    AnalysisReportUploadGQFilterSet,
    AnalysisReportSnapshotGQFilterSet,
)
from .serializers import (
    AnalysisReportConfigurationSerializer,
    AnalysisReportUploadMetadataSerializer,
    AnalysisReportContainerContentConfigurationSerializer,
    AnalysisReportContainerStyleSerializer,
)


def _get_qs(model, info, project_field):
    qs = model.objects.filter(**{
        # Filter by project
        project_field: info.context.active_project,
    })
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return qs
    return qs.model.objects.none()


def get_analysis_qs(info):
    return _get_qs(Analysis, info, 'project')


def get_analysis_pillar_qs(info):
    return _get_qs(AnalysisPillar, info, 'analysis__project')


def get_analytical_statement_qs(info):
    return _get_qs(AnalyticalStatement, info, 'analysis_pillar__analysis__project')


def get_analysis_report_qs(info):
    return _get_qs(AnalysisReport, info, 'analysis__project')


def get_analysis_report_upload_qs(info):
    return _get_qs(AnalysisReportUpload, info, 'report__analysis__project')


def get_analysis_report_snaphost_qs(info):
    return _get_qs(AnalysisReportSnapshot, info, 'report__analysis__project')


class AnalyticalStatementEntryType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatementEntry
        only_fields = (
            'id',
            'order',
        )

    entry = graphene.Field(EntryType, required=True)
    entry_id = graphene.ID(required=True)
    analytical_statement = graphene.ID(source='analytical_statement_id', required=True)

    @staticmethod
    def resolve_entry(root, info, **_):
        if has_select_related(root, 'entry'):
            return getattr(root, 'entry')
        # Use Dataloader to load the data
        return info.context.dl.entry.entry.load(root.entry_id)


class AnalyticalStatementType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatement
        only_fields = (
            'id',
            'statement',
            'report_text',
            'information_gaps',
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
        return info.context.dl.analysis.analytical_statement_analyzed_entries.load(root.id)

    @staticmethod
    def resolve_entries(root, info, **_):
        return info.context.dl.analysis.analytical_statement_entries.load(root.id)


class AnalysisPillarDiscardedEntryType(DjangoObjectType):
    class Meta:
        model = DiscardedEntry
        only_fields = ('id',)

    analysis_pillar = graphene.ID(source='analysis_pillar_id')
    entry = graphene.Field(EntryType, required=True)
    entry_id = graphene.ID(required=True)
    tag = graphene.Field(DiscardedEntryTagTypeEnum, required=True)
    tag_display = EnumDescription(source='get_tag_display', required=True)

    @staticmethod
    def resolve_entry(root, info, **_):
        if has_select_related(root, 'entry'):
            return getattr(root, 'entry')
        # Use Dataloader to load the data
        return info.context.dl.entry.entry.load(root.entry_id)


class AnalysisPillarEntryListType(CustomDjangoListObjectType):
    class Meta:
        model = Entry
        filterset_class = AnalysisPillarEntryGQFilterSet


class AnalysisPillarDiscardedEntryListType(CustomDjangoListObjectType):
    class Meta:
        model = DiscardedEntry
        filterset_class = AnalysisPillarDiscardedEntryGqlFilterSet


class AnalysisPillarType(ClientIdMixin, UserResourceMixin, DjangoObjectType):
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
    discarded_entries = DjangoPaginatedListObjectField(
        AnalysisPillarDiscardedEntryListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    # Generated
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
    def resolve_discarded_entries(root, info, **_):
        return DiscardedEntry.objects.filter(analysis_pillar=root)

    @staticmethod
    def resolve_entries(root, info, **kwargs):
        # This is the base queryset using Pillar, additional filters are applied through DjangoPaginatedListObjectField
        # filtering out the entries whose lead published_on date is less than analysis end_date
        return root.get_entries_qs(
            queryset=get_entry_qs(info),
            only_discarded=kwargs.get('discarded'),  # NOTE: From AnalysisPillarEntryGQFilterSet.discarded
        )


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


# NLP Trigger queries
class AnalysisTopicModelClusterType(DjangoObjectType):
    entries = graphene.List(EntryType, required=True)

    class Meta:
        model = TopicModelCluster
        only_fields = (
            'id',
        )

    @staticmethod
    def resolve_entries(root: TopicModelCluster, info, **_):
        return info.context.dl.analysis.topic_model_cluster_entries.load(root.id)


class AnalysisTopicModelType(UserResourceMixin, DjangoObjectType):
    status = graphene.Field(TopicModelStatusEnum, required=True)
    clusters = graphene.List(AnalysisTopicModelClusterType, required=True)
    additional_filters = graphene.Field(EntriesFilterDataType)
    analysis_pillar = graphene.ID(source='analysis_pillar_id', required=True)

    class Meta:
        model = TopicModel
        only_fields = (
            'id',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return _get_qs(TopicModel, info, 'analysis_pillar__analysis__project')

    @staticmethod
    def resolve_clusters(root: TopicModel, info, **_):
        return root.topicmodelcluster_set.all()


class AnalysisAutomaticSummaryType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = AutomaticSummary
        only_fields = (
            'id',
            'summary',
        )

    status = graphene.Field(AutomaticSummaryStatusEnum, required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return _get_qs(AutomaticSummary, info, 'project')


class AnalyticalStatementNGramType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatementNGram
        only_fields = (
            'id',
        )

    class AnalyticalStatementNGramDataType(graphene.ObjectType):
        word = graphene.String(required=True)
        count = graphene.Int(required=True)

    status = graphene.Field(AnalyticalStatementNGramStatusEnum, required=True)

    # Ngrams data
    unigrams = graphene.List(AnalyticalStatementNGramDataType, required=True)
    bigrams = graphene.List(AnalyticalStatementNGramDataType, required=True)
    trigrams = graphene.List(AnalyticalStatementNGramDataType, required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return _get_qs(AnalyticalStatementNGram, info, 'project')

    @staticmethod
    def render_grams(dict_value):
        return [
            dict(word=word, count=count)
            for word, count in dict_value.items()
        ]

    @classmethod
    def resolve_unigrams(cls, root: AnalyticalStatementNGram, info, **_):
        return cls.render_grams(root.unigrams)

    @classmethod
    def resolve_bigrams(cls, root: AnalyticalStatementNGram, info, **_):
        return cls.render_grams(root.bigrams)

    @classmethod
    def resolve_trigrams(cls, root: AnalyticalStatementNGram, info, **_):
        return cls.render_grams(root.trigrams)


class AnalyticalStatementEntryGeoType(DjangoObjectType):
    class Meta:
        model = AnalyticalStatementGeoEntry
        only_fields = (
            'id',
        )

    entry = graphene.Field(EntryType, required=True)
    entry_id = graphene.ID(required=True)
    data = graphene.List(graphene.NonNull(
        type('AnalyticalStatementEntryGeoDataType', (graphene.ObjectType,), {
            'ent': graphene.String(),
            'offset_start': graphene.Int(),
            'offset_end': graphene.Int(),
            'geoids': graphene.List(graphene.NonNull(
                type('AnalyticalStatementEntryGeoIDsDataType', (graphene.ObjectType,), {
                    'match': graphene.String(),
                    'geonameid': graphene.Int(),
                    'latitude': graphene.Float(),
                    'longitude': graphene.Float(),
                    'featurecode': graphene.String(),
                    'countrycode': graphene.String(),
                })
            ))
        })
    ))

    @staticmethod
    def resolve_entry(root, info, **_):
        if has_select_related(root, 'entry'):
            return getattr(root, 'entry')
        # Use Dataloader to load the data
        return info.context.dl.entry.entry.load(root.entry_id)


class AnalyticalStatementGeoTaskType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = AnalyticalStatementGeoTask
        only_fields = (
            'id',
        )

    status = graphene.Field(AnalyticalStatementGeoTaskStatusEnum, required=True)
    entry_geo = graphene.List(AnalyticalStatementEntryGeoType, required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return _get_qs(AnalyticalStatementGeoTask, info, 'project')

    @staticmethod
    def resolve_entry_geo(root, info, **_):
        return root.entry_geos.all()


class EntryGeoCentroidData(graphene.ObjectType):
    centroid = PointScalar(required=True)
    count = graphene.Int(required=True)


class AnalysisReportUploadType(DjangoObjectType):
    class Meta:
        model = AnalysisReportUpload
        only_fields = (
            'id',
            'file',  # TODO Dataloader
        )

    report = graphene.ID(source='report_id', required=True)
    type = graphene.Field(AnalysisReportUploadTypeEnum, required=True)
    metadata = graphene.Field(generate_type_for_serializer(
        'AnalysisReportUploadMetadataType',
        serializer_class=AnalysisReportUploadMetadataSerializer,
    ))

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analysis_report_upload_qs(info)


class AnalysisReportContainerDataType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisReportContainerData
        only_fields = (
            'id',
            'upload',  # AnalysisReportUploadType  # TODO: Dataloader
            'data',  # NOTE: This is Generic for now
        )


class AnalysisReportContainerType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisReportContainer
        only_fields = (
            'id',
            'row',
            'column',
            'width',
            'height',
        )

    content_type = graphene.Field(AnalysisReportContainerContentTypeEnum, required=True)
    report = graphene.ID(source='report_id', required=True)

    style = graphene.Field(
        generate_type_for_serializer(
            'AnalysisReportContainerStyleType',
            serializer_class=AnalysisReportContainerStyleSerializer,
            update_cache=True,
        )
    )
    # Content metadata
    content_configuration = graphene.Field(
        generate_type_for_serializer(
            'AnalysisReportContainerContentConfigurationType',
            serializer_class=AnalysisReportContainerContentConfigurationSerializer,
        )
    )
    content_data = graphene.List(graphene.NonNull(AnalysisReportContainerDataType), required=True)

    def resolve_content_data(root, info, **_):
        # TODO: Dataloader
        return root.analysisreportcontainerdata_set.all()


class AnalysisReportType(DjangoObjectType):
    class Meta:
        model = AnalysisReport
        only_fields = (
            'id',
            'is_public',
            'slug',
            'title',
            'sub_title',
        )

    analysis = graphene.ID(source='analysis_id', required=True)
    configuration = graphene.Field(generate_type_for_serializer(
        'AnalysisReportConfigurationType',
        serializer_class=AnalysisReportConfigurationSerializer,
    ))

    containers = graphene.List(
        graphene.NonNull(
            AnalysisReportContainerType
        ),
        required=True
    )
    organizations = graphene.List(graphene.NonNull(OrganizationType), required=True)
    uploads = graphene.List(graphene.NonNull(AnalysisReportUploadType), required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analysis_report_qs(info)

    def resolve_organizations(root, info, **_):
        # TODO: Dataloader
        return root.organizations.all()

    def resolve_uploads(root, info, **_):
        # TODO: Dataloader
        return root.analysisreportupload_set.all()

    def resolve_containers(root, info, **_):
        # TODO: Dataloader
        return root.analysisreportcontainer_set.all()


class AnalysisReportSnapshotType(DjangoObjectType):
    class Meta:
        model = AnalysisReportSnapshot
        only_fields = (
            'id',
            'published_on',
        )

    report = graphene.ID(source='report_id', required=True)
    published_by = graphene.Field(UserType, required=True)
    report_data_file = graphene.Field(FileFieldType)

    @staticmethod
    def resolve_published_by(root, info, **_):
        return resolve_user_field(root, info, 'published_by')

    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_analysis_report_snaphost_qs(info)


class AnalysisReportListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisReport
        filterset_class = AnalysisReportGQFilterSet


class AnalysisReportUploadListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisReportUpload
        filterset_class = AnalysisReportUploadGQFilterSet


class AnalysisReportSnapshotListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisReportSnapshot
        filterset_class = AnalysisReportSnapshotGQFilterSet


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

    # Custom entry nodes
    entries_geo_data = graphene.Field(
        graphene.List(
            graphene.NonNull(EntryGeoCentroidData),
            required=True,
        ),
        entries_id=graphene.List(graphene.NonNull(graphene.ID), required=True),
    )

    # NLP queries
    analysis_topic_model = DjangoObjectField(AnalysisTopicModelType)
    analysis_automatic_summary = DjangoObjectField(AnalysisAutomaticSummaryType)
    analysis_automatic_ngram = DjangoObjectField(AnalyticalStatementNGramType)
    analysis_geo_task = DjangoObjectField(AnalyticalStatementGeoTaskType)

    # Report
    analysis_report = DjangoObjectField(AnalysisReportType)
    analysis_reports = DjangoPaginatedListObjectField(
        AnalysisReportListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    analysis_report_upload = DjangoObjectField(AnalysisReportUploadType)
    analysis_report_uploads = DjangoPaginatedListObjectField(
        AnalysisReportUploadListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    analysis_report_snapshot = DjangoObjectField(AnalysisReportSnapshotType)
    analysis_report_snapshots = DjangoPaginatedListObjectField(
        AnalysisReportSnapshotListType,
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

    @staticmethod
    def resolve_analysis_reports(root, info, **kwargs) -> models.QuerySet:
        return get_analysis_report_qs(info)

    @staticmethod
    def resolve_analysis_report_uploads(root, info, **kwargs) -> models.QuerySet:
        return get_analysis_report_upload_qs(info)

    @staticmethod
    def resolve_entries_geo_data(_, info, entries_id):
        entry_qs = get_entry_qs(info).filter(id__in=entries_id)
        entry_geo_area_id_qs = Attribute.objects.filter(
            entry__in=entry_qs,
            widget__widget_id=Widget.WidgetType.GEO,
        ).values(
            geo_area_id=Cast(
                models.Func(
                    models.F('data__value'),
                    function='jsonb_array_elements_text',
                ),
                output_field=models.IntegerField(),
            )
        )
        geo_area_centroids_map = {
            geo_area_id: centroid
            for geo_area_id, centroid in GeoArea.objects.filter(
                id__in=entry_geo_area_id_qs.values('geo_area_id')
            ).exclude(IsEmpty('centroid')).values_list('id', 'centroid')
            if centroid is not None
        }
        return [
            dict(
                centroid=geo_area_centroids_map[geo_area_id],
                count=count,
            )
            for geo_area_id, count in (
                entry_geo_area_id_qs
                .order_by().values('geo_area_id')
                .annotate(count=models.Count('*'))
                .values_list('geo_area_id', 'count')
            )
            if geo_area_id in geo_area_centroids_map
        ]
