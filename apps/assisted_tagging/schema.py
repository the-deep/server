import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.enums import EnumDescription
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP

from .models import (
    DraftEntry,
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    AssistedTaggingPrediction,
    MissingPredictionReview,
    WrongPredictionReview,
)
from .enums import (
    DraftEntryPredictionStatusEnum,
    AssistedTaggingPredictionDataTypeEnum,
)


# -- Global Level
class AssistedTaggingModelVersionType(DjangoObjectType):
    class Meta:
        model = AssistedTaggingModelVersion
        fields = (
            'id',
            'version',
        )


class AssistedTaggingModelType(DjangoObjectType):
    latest_version = graphene.Field(AssistedTaggingModelVersionType)
    versions = graphene.List(
        graphene.NonNull(AssistedTaggingModelVersionType)
    )

    class Meta:
        model = AssistedTaggingModel
        fields = (
            'id',
            'name',
            'model_id',
        )

    @staticmethod
    def resolve_versions(root, info, **kwargs):
        return root.versions.all()   # TODO: Dataloaders

    @staticmethod
    def resolve_latest_version(root, info, **kwargs):
        return root.latest_version   # TODO: Dataloaders


class AssistedTaggingModelPredictionTagType(DjangoObjectType):
    class Meta:
        model = AssistedTaggingModelPredictionTag
        fields = (
            'id',
            'name',
            'tag_id',
            'is_deprecated',
            'hide_in_analysis_framework_mapping',
        )


class AssistedTaggingRootQueryType(graphene.ObjectType):
    tagging_model = DjangoObjectField(AssistedTaggingModelType)
    tagging_models = graphene.List(
        graphene.NonNull(AssistedTaggingModelType),
    )

    prediction_tag = DjangoObjectField(AssistedTaggingModelPredictionTagType)
    prediction_tags = graphene.List(
        graphene.NonNull(AssistedTaggingModelPredictionTagType)
    )

    @staticmethod
    def resolve_tagging_models(root, info, **kwargs):
        return AssistedTaggingModel.objects.all()

    @staticmethod
    def resolve_prediction_tags(root, info, **kwargs):
        return AssistedTaggingModelPredictionTag.objects.all()


# -- Project Level
def get_draft_entry_qs(info):
    qs = DraftEntry.objects.filter(project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return qs
    return qs.none()


class WrongPredictionReviewType(UserResourceMixin, DjangoObjectType):
    prediction = graphene.ID(source='prediction_id', required=True)

    class Meta:
        model = WrongPredictionReview
        fields = (
            'id',
        )


class AssistedTaggingPredictionType(DjangoObjectType):
    model_version = graphene.ID(source='model_version_id', required=True)
    draft_entry = graphene.ID(source='draft_entry_id', required=True)
    data_type = graphene.Field(AssistedTaggingPredictionDataTypeEnum, required=True)
    data_type_display = EnumDescription(source='get_data_type_display', required=True)
    category = graphene.ID(source='category_id')
    tag = graphene.ID(source='tag_id')
    wrong_prediction_reviews = graphene.List(
        graphene.NonNull(WrongPredictionReviewType),
    )

    class Meta:
        model = AssistedTaggingPrediction
        fields = (
            'id',
            'value',
            'prediction',
            'threshold',
            'is_selected',
        )

    @staticmethod
    def resolve_wrong_prediction_reviews(root, info, **kwargs):
        return root.wrong_prediction_reviews.all()   # TODO: Dataloaders


class MissingPredictionReviewType(UserResourceMixin, DjangoObjectType):
    category = graphene.ID(source='category_id', required=True)
    tag = graphene.ID(source='tag_id', required=True)
    draft_entry = graphene.ID(source='draft_entry_id', required=True)

    class Meta:
        model = MissingPredictionReview
        fields = (
            'id',
        )


class DraftEntryType(DjangoObjectType):
    # TODO: Maybe use dataloader or not since this is fetched one at a time.
    prediction_status = graphene.Field(DraftEntryPredictionStatusEnum, required=True)
    prediction_status_display = EnumDescription(source='get_prediction_status_display', required=True)
    predictions = graphene.List(
        graphene.NonNull(AssistedTaggingPredictionType)
    )
    missing_prediction_reviews = graphene.List(
        graphene.NonNull(MissingPredictionReviewType),
    )

    class Meta:
        model = DraftEntry
        fields = (
            'id',
            'excerpt',
            'prediction_received_at',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_draft_entry_qs(info)

    @staticmethod
    def resolve_predictions(root, info, **kwargs):
        return root.predictions.all()   # TODO: Need Dataloaders?

    @staticmethod
    def resolve_missing_prediction_reviews(root, info, **kwargs):
        return root.missing_prediction_reviews.all()   # TODO: Need Dataloaders?


# This is attached to project type.
class AssistedTaggingQueryType(graphene.ObjectType):
    draft_entry = DjangoObjectField(DraftEntryType)
