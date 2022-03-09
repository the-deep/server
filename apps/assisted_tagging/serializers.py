from django.db import transaction
from rest_framework import serializers

from user_resource.serializers import UserResourceSerializer, UserResourceCreatedMixin
from deep.serializers import ProjectPropertySerializerMixin, TempClientIdMixin
from analysis_framework.models import Widget

from .models import (
    AssistedTaggingPrediction,
    DraftEntry,
    MissingPredictionReview,
    PredictionTagAnalysisFrameworkWidgetMapping,
    WrongPredictionReview,
)
from .tasks import AsssistedTaggingTask


# --- Callback Serializers
class ModelPredictionCallbackSerializer(serializers.Serializer):
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


class AssistedTaggingDraftEntryPredictionCallbackSerializer(serializers.Serializer):
    client_id = serializers.CharField()
    model_preds = ModelPredictionCallbackSerializer(many=True)

    def validate(self, data):
        client_id = data['client_id']
        try:
            data['draft_entry'] = AsssistedTaggingTask.get_draft_entry_from_client_id(client_id)
        except Exception as e:
            raise serializers.ValidationError({
                'client_id': str(e)
            })
        return data

    def create(self, validated_data):
        draft_entry = validated_data['draft_entry']
        if draft_entry.prediction_status == DraftEntry.PredictionStatus.DONE:
            return draft_entry
        return AsssistedTaggingTask.save_entry_draft_data(draft_entry, validated_data)


# ---------- Graphql ---------------------------
class DraftEntryGqlSerializer(ProjectPropertySerializerMixin, UserResourceCreatedMixin, serializers.ModelSerializer):
    class Meta:
        model = DraftEntry
        fields = (
            'lead',
            'excerpt',
        )

    def validate_lead(self, lead):
        if lead.project != self.project:
            raise serializers.ValidationError('Only lead from current project are allowed.')
        return lead

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        data['project'] = self.project
        return data

    def create(self, data):
        instance = super().create(data)
        transaction.on_commit(
            lambda: AsssistedTaggingTask.send_trigger_request_to_extractor(instance)
        )
        return instance

    def update(self, *_):
        raise Exception('Update not allowed')


class WrongPredictionReviewGqlSerializer(UserResourceSerializer, serializers.ModelSerializer):
    class Meta:
        model = WrongPredictionReview
        fields = (
            'prediction',
        )

    def validate_prediction(self, prediction):
        if prediction.draft_entry.project != self.context['request'].active_project:
            raise serializers.ValidationError('Prediction not part of the active project.')
        return prediction

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        return data


class MissingPredictionReviewGqlSerializer(UserResourceSerializer):
    class Meta:
        model = MissingPredictionReview
        fields = (
            'draft_entry',
            'tag',
            'category',
        )

    def validate_draft_entry(self, draft_entry):
        if draft_entry.project != self.context['request'].active_project:
            raise serializers.ValidationError('Draft Entry not part of the active project.')
        return draft_entry

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        return data


# ------------------------ Analysis Framework ---------------------------------------------
class PredictionTagAnalysisFrameworkMapSerializer(TempClientIdMixin, serializers.ModelSerializer):
    TAG_NOT_REQUIRED_FOR_WIDGET_TYPE = [
        Widget.WidgetType.GEO,
    ]

    class Meta:
        model = PredictionTagAnalysisFrameworkWidgetMapping
        fields = (
            'id',
            'widget',
            'tag',
            'association',
            'client_id',  # From TempClientIdMixin
        )

    def validate(self, data):
        tag = data.get('tag', self.instance and self.instance.tag)
        association = data.get('association', self.instance and self.instance.association)
        widget = data.get('widget', self.instance and self.instance.widget)
        skip_tag = widget.widget_id not in self.TAG_NOT_REQUIRED_FOR_WIDGET_TYPE
        if tag is None and not skip_tag:
            raise serializers.ValidationError(dict(
                tag='Tag is required for this widget.'
            ))
        if association is None and not skip_tag:
            raise serializers.ValidationError(dict(
                association='Association is required for this widget.'
            ))
        return data
