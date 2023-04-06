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
)

from .models import DeeplTrackBaseModel


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


# -- Lead
class LeadExtractCallbackSerializer(BaseCallbackSerializer):
    """
    Serialize deepl extractor
    """
    url = serializers.CharField()
    extraction_status = serializers.IntegerField()  # 0 = Failed, 1 = Success
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
        if data['extraction_status'] == 1 and data.get('text_path') in [None, '']:
            raise serializers.ValidationError({
                'text_path': 'text_path is required when extraction_status is success/1'
            })
        if data['extraction_status'] == 1:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages']:
                if key not in data:
                    errors[key] = f'<{key}> is missing. Required when the extraction is 1 (Success)'
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        success = data['extraction_status'] == 1
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
class UnifiedConnectorLeadExtractCallbackSerializer(BaseCallbackSerializer):
    """
    Serialize deepl extractor
    """
    url = serializers.CharField()
    extraction_status = serializers.IntegerField()  # 0 = Failed, 1 = Success
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
        if data['extraction_status'] == 1:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages']:
                if key not in data:
                    errors[key] = f'<{key}> is missing. Required when the extraction is 1 (Success)'
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        success = data['extraction_status'] == 1
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


# -- Analysis
class DeeplServerBaseCallbackSerializer(BaseCallbackSerializer):
    class Status(models.IntegerChoices):
        # NOTE: Defined by NLP
        SUCCESS = 2, 'Success'
        FAILED = 3, 'Failed'
        INPUT_URL_PROCESS_FAILED = 4, 'Input url process failed'

    status = serializers.ChoiceField(choices=Status.choices)


class EntriesCollectionBaseCallbackSerializer(DeeplServerBaseCallbackSerializer):
    model: Type[DeeplTrackBaseModel]

    def create(self, validated_data):
        obj = validated_data['object']
        if validated_data['status'] == self.Status.SUCCESS:
            self.nlp_handler.save_data(obj, validated_data)
        else:
            obj.status = self.model.Status.FAILED
            obj.save(update_fields=('status',))
        return obj


class AnalysisTopicModelCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = TopicModel
    nlp_handler = AnalysisTopicModelHandler
    presigned_s3_url = serializers.URLField()


class AnalysisAutomaticSummaryCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = AutomaticSummary
    nlp_handler = AnalysisAutomaticSummaryHandler
    presigned_s3_url = serializers.URLField()


class AnalyticalStatementNGramCallbackSerializer(EntriesCollectionBaseCallbackSerializer):
    model = AnalyticalStatementNGram
    nlp_handler = AnalyticalStatementNGramHandler
    presigned_s3_url = serializers.URLField()
