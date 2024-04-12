import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from django.db.models import Prefetch
from assisted_tagging.filters import DraftEntryFilterSet

from utils.graphene.enums import EnumDescription
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP

from geo.schema import (
    ProjectGeoAreaType,
)
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.types import CustomDjangoListObjectType
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
        only_fields = (
            'id',
            'version',
        )


class AssistedTaggingModelType(DjangoObjectType):
    versions = graphene.List(
        graphene.NonNull(AssistedTaggingModelVersionType)
    )

    class Meta:
        model = AssistedTaggingModel
        only_fields = (
            'id',
            'name',
            'model_id',
        )

    @staticmethod
    def resolve_versions(root, info, **kwargs):
        return root.versions.all()   # NOTE: Prefetched


class AssistedTaggingModelPredictionTagType(DjangoObjectType):
    parent_tag = graphene.ID(source='parent_tag_id')

    class Meta:
        model = AssistedTaggingModelPredictionTag
        only_fields = (
            'id',
            'name',
            'group',
            'tag_id',
            'is_category',
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
        return AssistedTaggingModel.objects.prefetch_related(
            Prefetch(
                'versions',
                queryset=AssistedTaggingModelVersion.objects.order_by('-version'),
            ),
        ).all()

    @staticmethod
    def resolve_prediction_tags(root, info, **kwargs):
        return AssistedTaggingModelPredictionTag.objects.all()


# -- Project Level
def get_draft_entry_qs(info):  # TODO use dataloader
    qs = DraftEntry.objects.filter(project=info.context.active_project).order_by('page', 'text_order')
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return qs
    return qs.none()


def get_draft_entry_with_filter_qs(info, filters):
    qs = DraftEntry.objects.filter(project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return DraftEntryFilterSet(queryset=qs, data=filters).qs
    return qs.none()


class WrongPredictionReviewType(UserResourceMixin, DjangoObjectType):
    prediction = graphene.ID(source='prediction_id', required=True)

    class Meta:
        model = WrongPredictionReview
        only_fields = (
            'id',
        )


class AssistedTaggingPredictionType(DjangoObjectType):
    model_version = graphene.ID(source='model_version_id', required=True)
    draft_entry = graphene.ID(source='draft_entry_id', required=True)
    data_type = graphene.Field(AssistedTaggingPredictionDataTypeEnum, required=True)
    data_type_display = EnumDescription(source='get_data_type_display', required=True)
    category = graphene.ID(source='category_id')
    tag = graphene.ID(source='tag_id')

    class Meta:
        model = AssistedTaggingPrediction
        only_fields = (
            'id',
            'value',
            'prediction',
            'threshold',
            'is_selected',
        )
    '''
    NOTE: model_version_deepl_model_id and wrong_prediction_review are not included here because they are not used in client
    '''


class MissingPredictionReviewType(UserResourceMixin, DjangoObjectType):
    category = graphene.ID(source='category_id', required=True)
    tag = graphene.ID(source='tag_id', required=True)
    draft_entry = graphene.ID(source='draft_entry_id', required=True)

    class Meta:
        model = MissingPredictionReview
        only_fields = (
            'id',
        )


class DraftEntryType(DjangoObjectType):
    prediction_status = graphene.Field(DraftEntryPredictionStatusEnum, required=True)
    prediction_status_display = EnumDescription(source='get_prediction_status_display', required=True)
    prediction_tags = graphene.List(
        graphene.NonNull(AssistedTaggingPredictionType)
    )
    geo_areas = graphene.List(
        graphene.NonNull(ProjectGeoAreaType)
    )

    class Meta:
        model = DraftEntry
        only_fields = (
            'id',
            'excerpt',
            'prediction_received_at',
        )

    @staticmethod
    def get_custom_queryset(root, info, **kwargs):
        return get_draft_entry_qs(info)

    @staticmethod
    def resolve_prediction_tags(root, info, **kwargs):
        return info.context.dl.assisted_tagging.draft_entry_predications.load(root.pk)

    @staticmethod
    def resolve_geo_areas(root, info, **_):
        return info.context.dl.geo.draft_entry_geo_area.load(root.pk)


class DraftEntryListType(CustomDjangoListObjectType):
    class Meta:
        model = DraftEntry
        filterset_class = DraftEntryFilterSet


# This is attached to project type.


class AssistedTaggingQueryType(graphene.ObjectType):
    draft_entry = DjangoObjectField(DraftEntryType)
    draft_entries = DjangoPaginatedListObjectField(
        DraftEntryListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        ),
    )

    @staticmethod
    def resolve_draft_entries(root, info, **_):
        return get_draft_entry_qs(info)
