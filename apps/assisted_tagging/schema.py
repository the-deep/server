import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.enums import EnumDescription
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP

from .filters import (
    AssistedTaggingModelGQFilterSet,
    AssistedTaggingModelPredictionTagGQFilterSet,
)
from .models import (
    DraftEntry,
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    AssistedTaggingPrediction,
    MissingPredictionReview,
    WrongPredictionReview,
    PredictionTagAnalysisFrameworkWidgetMapping,
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
            'tag_id',
            'is_depricated',
        )


class AssistedTaggingModelListType(CustomDjangoListObjectType):
    class Meta:
        model = AssistedTaggingModel
        filterset_class = AssistedTaggingModelGQFilterSet


class AssistedTaggingModelPredictionTagListType(CustomDjangoListObjectType):
    class Meta:
        model = AssistedTaggingModelPredictionTag
        filterset_class = AssistedTaggingModelPredictionTagGQFilterSet


class AssistedTaggingRootQueryType(graphene.ObjectType):
    tagging_model = DjangoObjectField(AssistedTaggingModelType)
    tagging_models = DjangoPaginatedListObjectField(
        AssistedTaggingModelListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )

    prediction_tag = DjangoObjectField(AssistedTaggingModelPredictionTagType)
    prediction_tags = DjangoPaginatedListObjectField(
        AssistedTaggingModelPredictionTagListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )


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


# ----- Additional Types --------
class AnalysisFrameworkPredictionMappingType(DjangoObjectType):
    widget = graphene.ID(source='widget_id', required=True)
    tag = graphene.ID(source='tag_id', required=True)

    class Meta:
        model = PredictionTagAnalysisFrameworkWidgetMapping
        fields = (
            'id',
            'widget',
            'tag',
            'association',
        )
