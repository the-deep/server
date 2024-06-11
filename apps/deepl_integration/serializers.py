from typing import Type, List, Dict
import logging
from rest_framework import serializers

from django.db import transaction, models

from deepl_integration.handlers import (
    BaseHandler,
    AssistedTaggingDraftEntryHandler,
    LeadExtractionHandler,
    UnifiedConnectorLeadHandler,
    AnalysisTopicModelHandler,
    AnalysisAutomaticSummaryHandler,
    AnalyticalStatementNGramHandler,
    AnalyticalStatementGeoHandler,
    AutoAssistedTaggingDraftEntryHandler
)

from deduplication.tasks.indexing import index_lead_and_calculate_duplicates
from assisted_tagging.models import (
    AssistedTaggingPrediction,
    DraftEntry,
)
from unified_connector.models import ConnectorLead
from lead.models import Lead
from analysis.models import (
    TopicModel,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
)

from .models import DeeplTrackBaseModel

logger = logging.getLogger(__name__)


class BaseCallbackSerializer(serializers.Serializer):
    nlp_handler: Type[BaseHandler]

    client_id = serializers.CharField()

    def validate(self, data):
        client_id = data['client_id']
        try:
            data['object'] = self.nlp_handler.get_object_using_client_id(client_id)
        except Exception:
            logger.error('Failed to parse client id', exc_info=True)
            raise serializers.ValidationError({
                'client_id': 'Failed to parse client id',
            })
        return data


class DeeplServerBaseCallbackSerializer(BaseCallbackSerializer):
    class Status(models.IntegerChoices):
        # NOTE: Defined by NLP
        # INITIATED = 1, 'Initiated'  # Not needed or used by deep
        SUCCESS = 2, 'Success'
        FAILED = 3, 'Failed'
        INPUT_URL_PROCESS_FAILED = 4, 'Input url process failed'

    status = serializers.ChoiceField(choices=Status.choices)


class ImagePathSerializer(serializers.Serializer):
    page_number = serializers.IntegerField(required=True)
    images = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        default=[],
    )


class TablePathSerializer(serializers.Serializer):
    page_number = serializers.IntegerField(required=True)
    order = serializers.IntegerField(required=True)
    image_link = serializers.URLField(required=True)
    content_link = serializers.URLField(required=True)


# -- Lead
class LeadExtractCallbackSerializer(DeeplServerBaseCallbackSerializer):
    """
    Serialize deepl extractor
    """
    url = serializers.CharField(required=False)
    # Data fields
    images_path = serializers.ListSerializer(
        child=ImagePathSerializer(required=True),
        required=False
    )
    tables_path = serializers.ListSerializer(
        child=TablePathSerializer(required=True),
        required=False
    )
    text_path = serializers.CharField(required=False, allow_null=True)
    total_words_count = serializers.IntegerField(required=False, default=0, allow_null=True)
    total_pages = serializers.IntegerField(required=False, default=0, allow_null=True)
    text_extraction_id = serializers.UUIDField(required=False, allow_null=True)
    nlp_handler = LeadExtractionHandler

    def validate(self, data):
        data = super().validate(data)
        # Additional validation
        if data['status'] == self.Status.SUCCESS and data.get('text_path') in [None, '']:
            raise serializers.ValidationError({
                'text_path': 'text_path is required when extraction status is success'
            })
        if data['status'] == self.Status.SUCCESS:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages', 'text_extraction_id']:
                if key not in data or data[key] is None:
                    errors[key] = (
                        f"<{key=} or {data.get('key')=}> is missing. Required when the extraction status is Success"
                    )
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data: List[Dict]):
        success = data['status'] == self.Status.SUCCESS
        lead = data['object']   # Added from validate
        if success:
            lead = self.nlp_handler.save_data(
                lead,
                data['text_path'],
                data.get('images_path', [])[:10],   # TODO: Support for more images, too much image will error.
                data.get('tables_path', []),
                data.get('total_words_count'),
                data.get('total_pages'),
                data.get('text_extraction_id'),
            )
            # Add to deduplication index
            transaction.on_commit(lambda: index_lead_and_calculate_duplicates.delay(lead.id))
            return lead
        lead.update_extraction_status(Lead.ExtractionStatus.FAILED)
        return lead


# -- Unified Connector
class UnifiedConnectorLeadExtractCallbackSerializer(DeeplServerBaseCallbackSerializer):
    """
    Serialize deepl extractor
    """
    # Data fields
    images_path = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False, default=[],
    )
    text_path = serializers.CharField(required=False, allow_null=True)
    total_words_count = serializers.IntegerField(required=False, default=0, allow_null=True)
    total_pages = serializers.IntegerField(required=False, default=0, allow_null=True)
    text_extraction_id = serializers.UUIDField(required=False, allow_null=True)

    nlp_handler = UnifiedConnectorLeadHandler

    def validate(self, data):
        data = super().validate(data)
        if data['status'] == self.Status.SUCCESS:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages', 'text_extraction_id']:
                if key not in data or data[key] is None:
                    errors[key] = (
                        f"<{key=} or {data.get('key')=}> is missing. Required when the extraction status is Success"
                    )
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        success = data['status'] == self.Status.SUCCESS
        connector_lead = data['object']   # Added from validate
        if success:
            return self.nlp_handler.save_data(
                connector_lead,
                data['text_path'],
                data.get('images_path', [])[:10],  # TODO: Support for more images, to much image will error.
                data['total_words_count'],
                data['total_pages'],
                data['text_extraction_id'],
            )
        connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.FAILED)
        return connector_lead


# --- AssistedTagging
class AssistedTaggingModelPredictionCallbackSerializer(serializers.Serializer):

    class ModelPredictionCallbackSerializerTagValue(serializers.Serializer):
        prediction = serializers.DecimalField(
            # From apps/assisted_tagging/models.py::AssistedTaggingPrediction::prediction
            max_digits=AssistedTaggingPrediction.prediction.field.max_digits,
            decimal_places=AssistedTaggingPrediction.prediction.field.decimal_places,
            required=False,
        )
        threshold = serializers.DecimalField(
            # From apps/assisted_tagging/models.py::AssistedTaggingPrediction::threshold
            max_digits=AssistedTaggingPrediction.threshold.field.max_digits,
            decimal_places=AssistedTaggingPrediction.threshold.field.decimal_places,
            required=False,
        )
        is_selected = serializers.BooleanField()

    # model_info = ModelInfoCallbackSerializer() removed from the DEEPL TODO Use different api for model information
    values = serializers.ListSerializer(
        child=serializers.CharField(),
        required=False,
    )
    tags = serializers.DictField(
        child=serializers.DictField(
            child=ModelPredictionCallbackSerializerTagValue(),
        ),
        required=False,
    )


class AutoAssistedTaggingModelPredicationCallBackSerializer(serializers.Serializer):
    class ModelPredictionCallbackSerializerTagValue(serializers.Serializer):
        predication = serializers.DecimalField(
            max_digits=AssistedTaggingPrediction.prediction.field.max_digits,
            decimal_places=AssistedTaggingPrediction.prediction.field.decimal_places,
            required=False,
        )
        threshold = serializers.DecimalField(
            # From apps/assisted_tagging/models.py::AssistedTaggingPrediction::threshold
            max_digits=AssistedTaggingPrediction.threshold.field.max_digits,
            decimal_places=AssistedTaggingPrediction.threshold.field.decimal_places,
            required=False,
        )
        is_selected = serializers.BooleanField()
    values = serializers.ListSerializer(
        child=serializers.CharField(),
        required=False,
    )
    tags = serializers.DictField(
        child=serializers.DictField(
            child=ModelPredictionCallbackSerializerTagValue(),
        ),
        required=False,
    )


class AssistedTaggingDraftEntryPredictionCallbackSerializer(BaseCallbackSerializer):
    model_tags = serializers.DictField(child=serializers.DictField())
    prediction_status = serializers.BooleanField()
    model_info = serializers.DictField()
    nlp_handler = AssistedTaggingDraftEntryHandler

    def create(self, validated_data):
        draft_entry = validated_data['object']
        if draft_entry.prediction_status == DraftEntry.PredictionStatus.DONE:
            return draft_entry
        return self.nlp_handler.save_data(
            draft_entry,
            validated_data,
        )


class AutoAssistedBlockPredicationCallbackSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    textOrder = serializers.IntegerField()
    text = serializers.CharField()
    relevant = serializers.BooleanField()
    prediction_status = serializers.BooleanField()
    classification = serializers.DictField(child=serializers.DictField())
    geolocations = serializers.DictField(child=serializers.DictField())


class AutoAssistedTaggingDraftEntryCallbackSerializer(BaseCallbackSerializer):
    entry_extraction_classification_path = serializers.URLField(required=True)
    text_extraction_id = serializers.CharField(required=True)
    status = serializers.IntegerField()
    nlp_handler = AutoAssistedTaggingDraftEntryHandler

    def create(self, validated_data):
        obj = validated_data['object']
        return self.nlp_handler.save_data(
            obj,
            validated_data['entry_extraction_classification_path'],
        )


class EntriesCollectionBaseCallbackSerializer(DeeplServerBaseCallbackSerializer):
    model: Type[DeeplTrackBaseModel]
    presigned_s3_url = serializers.URLField()

    def create(self, validated_data):
        obj = validated_data['object']
        if validated_data['status'] == self.Status.SUCCESS:
            self.nlp_handler.save_data(obj, validated_data)
        else:
            obj.status = self.model.Status.FAILED
            obj.save(update_fields=('status',))
        return obj


# -- Analysis
class AnalysisTopicModelCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = TopicModel
    nlp_handler = AnalysisTopicModelHandler


class AnalysisAutomaticSummaryCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = AutomaticSummary
    nlp_handler = AnalysisAutomaticSummaryHandler


class AnalyticalStatementNGramCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = AnalyticalStatementNGram
    nlp_handler = AnalyticalStatementNGramHandler


class AnalyticalStatementGeoCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = AnalyticalStatementGeoTask
    nlp_handler = AnalyticalStatementGeoHandler
