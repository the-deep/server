import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import (
    DraftEntry,
    MissingPredictionReview,
    WrongPredictionReview,
)
from .schema import (
    DraftEntryType,
    MissingPredictionReviewType,
    WrongPredictionReviewType,
)
from .serializers import (
    DraftEntryGqlSerializer,
    WrongPredictionReviewGqlSerializer,
    MissingPredictionReviewGqlSerializer,
    TriggeredDraftEntryGqlSerializer,
    UpdateDraftEntrySerializer
)


DraftEntryInputType = generate_input_type_for_serializer(
    'DraftEntryInputType',
    serializer_class=DraftEntryGqlSerializer,
)

WrongPredictionReviewInputType = generate_input_type_for_serializer(
    'WrongPredictionReviewInputType',
    serializer_class=WrongPredictionReviewGqlSerializer,
)

MissingPredictionReviewInputType = generate_input_type_for_serializer(
    'MissingPredictionReviewInputType',
    serializer_class=MissingPredictionReviewGqlSerializer,
)

TriggerDraftEntryInputType = generate_input_type_for_serializer(
    "TriggerDraftEntryInputType",
    serializer_class=TriggeredDraftEntryGqlSerializer
)

UpdateDraftEntryInputType = generate_input_type_for_serializer(
    "UpdateDraftEntryInputType",
    serializer_class=UpdateDraftEntrySerializer
)


class CreateDraftEntry(PsGrapheneMutation):
    class Arguments:
        data = DraftEntryInputType(required=True)
    model = DraftEntry
    serializer_class = DraftEntryGqlSerializer
    result = graphene.Field(DraftEntryType)
    permissions = [PP.Permission.CREATE_ENTRY]


class CreateMissingPredictionReview(PsGrapheneMutation):
    class Arguments:
        data = MissingPredictionReviewInputType(required=True)
    model = MissingPredictionReview
    serializer_class = MissingPredictionReviewGqlSerializer
    result = graphene.Field(MissingPredictionReviewType)
    permissions = [PP.Permission.CREATE_ENTRY]


class CreateWrongPredictionReview(PsGrapheneMutation):
    class Arguments:
        data = WrongPredictionReviewInputType(required=True)
    model = WrongPredictionReview
    serializer_class = WrongPredictionReviewGqlSerializer
    result = graphene.Field(MissingPredictionReviewType)
    permissions = [PP.Permission.CREATE_ENTRY]


class DeleteMissingPredictionReview(PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = MissingPredictionReview
    result = graphene.Field(MissingPredictionReviewType)
    permissions = [PP.Permission.CREATE_ENTRY]

    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(
            draft_entry__project=info.context.active_project,
            created_by=info.context.user,
        )


class DeleteWrongPredictionReview(PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = WrongPredictionReview
    result = graphene.Field(WrongPredictionReviewType)
    permissions = [PP.Permission.CREATE_ENTRY]

    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(
            predition__draft_entry__project=info.context.active_project,
            created_by=info.context.user,
        )

# auto draft_entry_create


class CreateAutoDraftEntry(PsGrapheneMutation):
    class Arguments:
        data = TriggerDraftEntryInputType(required=True)
    model = DraftEntry
    serializer_class = TriggeredDraftEntryGqlSerializer
    result = graphene.Field(DraftEntryType)
    permissions = [PP.Permission.CREATE_ENTRY]


class DiscardDraftEntry(PsGrapheneMutation):
    class Arguments:
        data = UpdateDraftEntryInputType(required=True)
        id = graphene.ID(required=True)
    model = DraftEntry
    serializer_class = UpdateDraftEntrySerializer
    result = graphene.Field(DraftEntryType)
    permissions = [PP.Permission.CREATE_ENTRY]


class AssistedTaggingMutationType(graphene.ObjectType):
    draft_entry_create = CreateDraftEntry.Field()
    missing_prediction_review_create = CreateMissingPredictionReview.Field()
    wrong_prediction_review_create = CreateWrongPredictionReview.Field()
    missing_prediction_review_delete = DeleteMissingPredictionReview.Field()
    wrong_prediction_review_delete = DeleteWrongPredictionReview.Field()
    auto_draft_entry_create = CreateAutoDraftEntry.Field()
    discard_draft_entry = DiscardDraftEntry.Field()
