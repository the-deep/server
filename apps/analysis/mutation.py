import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import AnalysisPillar, DiscardedEntry
from .schema import (
    get_analysis_pillar_qs,
    AnalysisPillarType,
    AnalysisPillarDiscardedEntryType,
)
from .serializers import (
    AnalysisPillarGqlSerializer,
    DiscardedEntryGqlSerializer,
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


class CreateAnalysisPillarDiscardedEntry(DiscardedEntriesMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = DiscardedEntryCreateInputType(required=True)
    model = DiscardedEntry
    serializer_class = DiscardedEntryGqlSerializer
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


class UpdateAnalysisPillarDiscardedEntry(DiscardedEntriesMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = DiscardedEntryUpdateInputType(required=True)
    model = DiscardedEntry
    serializer_class = DiscardedEntryGqlSerializer
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


class DeleteAnalysisPillarDiscardedEntry(DiscardedEntriesMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = DiscardedEntry
    result = graphene.Field(AnalysisPillarDiscardedEntryType)


class Mutation():
    # Analysis Pillar
    analysis_pillar_update = UpdateAnalysisPillar.Field()
    # Discarded Entry
    discarded_entry_create = CreateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_update = UpdateAnalysisPillarDiscardedEntry.Field()
    discarded_entry_delete = DeleteAnalysisPillarDiscardedEntry.Field()
