from rest_framework import serializers

from user_resource.serializers import UserResourceSerializer, UserResourceCreatedMixin
from deep.serializers import ProjectPropertySerializerMixin

from .models import (
    DraftEntry,
    MissingPredictionReview,
    WrongPredictionReview,
    PredictionTagAnalysisFrameworkWidgetMapping,
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
            max_digits=20,
            decimal_places=20,
            required=False,
        )
        threshold = serializers.DecimalField(
            # From apps/assisted_tagging/models.py::AssistedTaggingPrediction::threshold
            max_digits=20,
            decimal_places=20,
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
            'excerpt',
        )

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        data['project'] = self.project
        return data
    # TODO: Trigger send request to deepl server


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
class PredictionTagAnalysisFrameworkMapSerializer(serializers.ModelSerializer):
    association = serializers.DictField(required=False)

    class Meta:
        model = PredictionTagAnalysisFrameworkWidgetMapping
        fields = (
            'id',
            'widget',
            'tag',
            'association',
        )
