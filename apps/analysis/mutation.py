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
)
from .schema import (
    get_analysis_pillar_qs,
    AnalysisPillarType,
    AnalysisPillarDiscardedEntryType,
    AnalysisTopicModelType,
    AnalysisAutomaticSummaryType,
    AnalyticalStatementNGramType,
)
from .serializers import (
    AnalysisPillarGqlSerializer,
    DiscardedEntryGqlSerializer,
    AnalysisTopicModelSerializer,
    AnalysisAutomaticSummarySerializer,
    AnalyticalStatementNGramSerializer,
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


class RequiredPermissionMixin():
    permissions = [PP.Permission.VIEW_ENTRY, PP.Permission.CREATE_ANALYSIS_MODULE]


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


class Mutation():
    # Analysis Pillar
    analysis_pillar_update = UpdateAnalysisPillar.Field()
    # Discarded Entry
    discarded_entry_create = CreateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_update = UpdateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_delete = DeleteAnalysisPillarDiscardedEntry.Field()
    # NLP Trigger mutations
    trigger_topic_model = TriggerAnalysisTopicModel.Field()
    trigger_automatic_summary = TriggerAnalysisAutomaticSummary.Field()
    trigger_automatic_ngram = TriggerAnalysisAnalyticalStatementNGram.Field()
