import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import (
    AnalysisPillar,
    DiscardedEntry,
    TopicModel,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
    AnalysisReport,
    AnalysisReportUpload,
    AnalysisReportSnapshot,
)
from .schema import (
    get_analysis_pillar_qs,
    get_analysis_report_qs,
    get_analysis_report_upload_qs,
    AnalysisPillarType,
    AnalysisPillarDiscardedEntryType,
    AnalysisTopicModelType,
    AnalysisAutomaticSummaryType,
    AnalyticalStatementNGramType,
    AnalyticalStatementGeoTaskType,
    AnalysisReportType,
    AnalysisReportUploadType,
    AnalysisReportSnapshotType,
)
from .serializers import (
    AnalysisPillarGqlSerializer,
    DiscardedEntryGqlSerializer,
    AnalysisTopicModelSerializer,
    AnalysisAutomaticSummarySerializer,
    AnalyticalStatementNGramSerializer,
    AnalyticalStatementGeoTaskSerializer,
    AnalysisReportSerializer,
    AnalysisReportSnapshotSerializer,
    AnalysisReportUploadSerializer,
)


AnalysisPillarUpdateInputType = generate_input_type_for_serializer(
    'AnalysisPillarUpdateInputType',
    serializer_class=AnalysisPillarGqlSerializer,
    partial=True,
)

DiscardedEntryCreateInputType = generate_input_type_for_serializer(
    'DiscardedEntryCreateInputType',
    serializer_class=DiscardedEntryGqlSerializer,
)

DiscardedEntryUpdateInputType = generate_input_type_for_serializer(
    'DiscardedEntryUpdateInputType',
    serializer_class=DiscardedEntryGqlSerializer,
    partial=True,
)


AnalysisTopicModelCreateInputType = generate_input_type_for_serializer(
    'AnalysisTopicModelCreateInputType',
    serializer_class=AnalysisTopicModelSerializer,
)

AnalysisAutomaticSummaryCreateInputType = generate_input_type_for_serializer(
    'AnalysisAutomaticSummaryCreateInputType',
    serializer_class=AnalysisAutomaticSummarySerializer,
)

AnalyticalStatementNGramCreateInputType = generate_input_type_for_serializer(
    'AnalyticalStatementNGramCreateInputType',
    serializer_class=AnalyticalStatementNGramSerializer,
)

AnalyticalStatementGeoTaskInputType = generate_input_type_for_serializer(
    'AnalyticalStatementGeoTaskInputType',
    serializer_class=AnalyticalStatementGeoTaskSerializer,
)


# Analysi Report
AnalysisReportInputType = generate_input_type_for_serializer(
    'AnalysisReportInputType',
    serializer_class=AnalysisReportSerializer,
)
AnalysisReportInputUpdateType = generate_input_type_for_serializer(
    'AnalysisReportInputUpdateType',
    serializer_class=AnalysisReportSerializer,
    partial=True,
)

AnalysisReportSnapshotInputType = generate_input_type_for_serializer(
    'AnalysisReportSnapshotInputType',
    serializer_class=AnalysisReportSnapshotSerializer,
)

AnalysisReportUploadInputType = generate_input_type_for_serializer(
    'AnalysisReportUploadInputType',
    serializer_class=AnalysisReportUploadSerializer,
)


class RequiredPermissionMixin():
    permissions = [
        PP.Permission.VIEW_ENTRY,
        PP.Permission.CREATE_ANALYSIS_MODULE,
    ]


class AnalysisPillarMutationMixin(RequiredPermissionMixin):
    @classmethod
    def filter_queryset(cls, _, info):
        return get_analysis_pillar_qs(info)


class DiscardedEntriesMutationMixin(RequiredPermissionMixin):
    @classmethod
    def filter_queryset(cls, _, info):
        return DiscardedEntry.objects.filter(
            analysis_pillar__analysis__project=info.context.active_project,
        )


class AnalysisReportMutationMixin(RequiredPermissionMixin):
    @classmethod
    def filter_queryset(cls, _, info):
        return get_analysis_report_qs(info)


class AnalysisReportUploadMutationMixin(RequiredPermissionMixin):
    @classmethod
    def filter_queryset(cls, _, info):
        return get_analysis_report_upload_qs(info)


class UpdateAnalysisPillar(AnalysisPillarMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = AnalysisPillarUpdateInputType(required=True)
    model = AnalysisPillar
    serializer_class = AnalysisPillarGqlSerializer
    result = graphene.Field(AnalysisPillarType)

    @classmethod
    def get_serializer_context(cls, instance, context):
        return {
            **context,
            'analysis_end_date': instance.analysis.end_date,
        }


class CreateAnalysisPillarDiscardedEntry(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = DiscardedEntryCreateInputType(required=True)
    model = DiscardedEntry
    serializer_class = DiscardedEntryGqlSerializer
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


class UpdateAnalysisPillarDiscardedEntry(DiscardedEntriesMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = DiscardedEntryUpdateInputType(required=True)
    model = DiscardedEntry
    serializer_class = DiscardedEntryGqlSerializer
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


class DeleteAnalysisPillarDiscardedEntry(DiscardedEntriesMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = DiscardedEntry
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


# NLP Trigger mutations
class TriggerAnalysisTopicModel(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalysisTopicModelCreateInputType(required=True)
    model = TopicModel
    serializer_class = AnalysisTopicModelSerializer
    result = graphene.Field(AnalysisTopicModelType)


class TriggerAnalysisAutomaticSummary(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalysisAutomaticSummaryCreateInputType(required=True)
    model = AutomaticSummary
    serializer_class = AnalysisAutomaticSummarySerializer
    result = graphene.Field(AnalysisAutomaticSummaryType)


class TriggerAnalysisAnalyticalStatementNGram(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalyticalStatementNGramCreateInputType(required=True)
    model = AnalyticalStatementNGram
    serializer_class = AnalyticalStatementNGramSerializer
    result = graphene.Field(AnalyticalStatementNGramType)


class TriggerAnalysisAnalyticalGeoTask(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalyticalStatementGeoTaskInputType(required=True)
    model = AnalyticalStatementGeoTask
    serializer_class = AnalyticalStatementGeoTaskSerializer
    result = graphene.Field(AnalyticalStatementGeoTaskType)


# ----------------- Analysis Report ------------------------------------------
class CreateAnalysisReport(AnalysisReportMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalysisReportInputType(required=True)
    model = AnalysisReport
    serializer_class = AnalysisReportSerializer
    result = graphene.Field(AnalysisReportType)


class UpdateAnalysisReport(AnalysisReportMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = AnalysisReportInputUpdateType(required=True)
    model = AnalysisReport
    serializer_class = AnalysisReportSerializer
    result = graphene.Field(AnalysisReportType)

    @classmethod
    def get_serializer_context(cls, instance, context):
        return {
            **context,
            'report': instance,
        }


class DeleteAnalysisReport(AnalysisReportMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = AnalysisReport
    result = graphene.Field(AnalysisReportType)


# -- Snapshot
class CreateAnalysisReportSnapshot(RequiredPermissionMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalysisReportSnapshotInputType(required=True)
    model = AnalysisReportSnapshot
    serializer_class = AnalysisReportSnapshotSerializer
    result = graphene.Field(AnalysisReportSnapshotType)


# -- Uploads
class CreateAnalysisReportUpload(AnalysisReportUploadMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = AnalysisReportUploadInputType(required=True)
    model = AnalysisReportUpload
    serializer_class = AnalysisReportUploadSerializer
    result = graphene.Field(AnalysisReportUploadType)


class DeleteAnalysisReportUpload(AnalysisReportUploadMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = AnalysisReportUpload
    result = graphene.Field(AnalysisReportUploadType)


class Mutation():
    # Analysis Pillar
    analysis_pillar_update = UpdateAnalysisPillar.Field()
    # Discarded Entry
    discarded_entry_create = CreateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_update = UpdateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_delete = DeleteAnalysisPillarDiscardedEntry.Field()
    # NLP Trigger mutations
    trigger_analysis_topic_model = TriggerAnalysisTopicModel.Field()
    trigger_analysis_automatic_summary = TriggerAnalysisAutomaticSummary.Field()
    trigger_analysis_automatic_ngram = TriggerAnalysisAnalyticalStatementNGram.Field()
    trigger_analysis_geo_location = TriggerAnalysisAnalyticalGeoTask.Field()
    # Analysis Report
    analysis_report_create = CreateAnalysisReport.Field()
    analysis_report_update = UpdateAnalysisReport.Field()
    analysis_report_delete = DeleteAnalysisReport.Field()
    analysis_report_snapshot_create = CreateAnalysisReportSnapshot.Field()
    # -- Uploads
    analysis_report_upload_create = CreateAnalysisReportUpload.Field()
    analysis_report_upload_delete = DeleteAnalysisReportUpload.Field()
