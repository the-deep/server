from typing import Type
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

from utils.request import RequestHelper


class BaseCallbackSerializer(serializers.Serializer):
    nlp_handler: Type[BaseHandler]

    client_id = serializers.CharField()

    def validate(self, data):
        client_id = data['client_id']
        try:
            data['object'] = self.nlp_handler.get_object_using_client_id(client_id)
        except Exception as e:
            raise serializers.ValidationError({
                'client_id': str(e),
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


# -- Lead
class LeadExtractCallbackSerializer(DeeplServerBaseCallbackSerializer):
    """
    Serialize deepl extractor
    """
    url = serializers.CharField()
    # Data fields
    images_path = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False, default=[],
    )
    text_path = serializers.CharField(required=False)
    total_words_count = serializers.IntegerField(required=False, default=0)
    total_pages = serializers.IntegerField(required=False, default=0)

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
            for key in ['text_path', 'total_words_count', 'total_pages']:
                if key not in data:
                    errors[key] = f'<{key}> is missing. Required when the extraction status is Success'
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        success = data['status'] == self.Status.SUCCESS
        lead = data['object']   # Added from validate
        if success:
            lead = self.nlp_handler.save_data(
                lead,
                data['text_path'],
                data.get('images_path', [])[:10],   # TODO: Support for more images, too much image will error.
                data.get('total_words_count'),
                data.get('total_pages'),
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
    url = serializers.CharField()
    # Data fields
    images_path = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False, default=[],
    )
    text_path = serializers.CharField(required=False)
    total_words_count = serializers.IntegerField(required=False, default=0)
    total_pages = serializers.IntegerField(required=False, default=0)

    nlp_handler = UnifiedConnectorLeadHandler

    def validate(self, data):
        data = super().validate(data)
        if data['object'].url != data['url']:
            raise serializers.ValidationError({
                'url': 'Different url found provided vs original connector lead',
            })
        if data['status'] == self.Status.SUCCESS:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages']:
                if key not in data:
                    errors[key] = f'<{key}> is missing. Required when the extraction is Success'
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
            )
        connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.FAILED)
        return connector_lead


# --- AssistedTagging
class AssistedTaggingModelPredictionCallbackSerializer(serializers.Serializer):
    class ModelInfoCallbackSerializer(serializers.Serializer):
        id = serializers.CharField()
        version = serializers.CharField()

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

    model_info = ModelInfoCallbackSerializer()
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
    prediction_status = serializers.IntegerField()  # 0 -> Failure, 1 -> Success


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
    model_preds = AssistedTaggingModelPredictionCallbackSerializer(many=True)

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
    text = serializers.CharField()
    relevant = serializers.BooleanField()
    prediction_status = serializers.BooleanField()
    # classification = AutoAssistedTaggingModelPredicationCallBackSerializer()
    classification = serializers.DictField(child=serializers.DictField())


class AutoAssistedTaggingDraftEntryCallbackSerializer(BaseCallbackSerializer):
    entry_extraction_classification_path = serializers.URLField(required=True)
    text_extraction_id = serializers.CharField(required=True)
    status = serializers.IntegerField()
    nlp_handler = AutoAssistedTaggingDraftEntryHandler

    def create(self, validated_data):
        obj = validated_data['object']
        validated_data = RequestHelper(url=validated_data['entry_extraction_classification_path'], ignore_error=True).json()
        return self.nlp_handler.save_data(
            obj,
            validated_data
        )

# class AutoAssistedTaggingDraftEntryCallbackSerializer(BaseCallbackSerializer):
#     blocks = AutoAssistedBlockPredicationCallbackSerializer(many=True)
#     classification_model_info = serializers.DictField()
#     nlp_handler = AutoAssistedTaggingDraftEntryHandler

#     def create(self, validated_data):
#         return self.nlp_handler.save_data(
#             validated_data['object'],
#             validated_data
#         )


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
