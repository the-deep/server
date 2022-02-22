import requests
from rest_framework import serializers
from django.conf import settings

from entry.models import Entry

from . import constants
from .models import ModelInfo, ModelPrediction, ReviewTag, PredictionEnum


class ModelInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelInfo
        fields = '__all__'

    def create(self, validated_data):
        validated_data["version"] = constants.ALL_MODEL_VERSION
        model_info = super().create(validated_data)
        return model_info


class ModelPredictionSerializer(serializers.ModelSerializer):

    prediction_name = serializers.SerializerMethodField('prediction_name')

    def prediction_name(self, obj):
        return obj.prediction_enum.name

    class Meta:
        model = ModelPrediction
        fields = '__all__'


class ReviewTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewTag
        fields = '__all__'


class ModelPredictionRequestSerializer(serializers.Serializer):
    entry_ids = serializers.ListField(child=serializers.IntegerField())


def save_virtual_framework_tags():
    headers = {
        "Content-Type": "application/json"
    }
    resp = requests.get(f"{settings.EXTRACTOR_URL}/vf_tags", headers=headers)
    data = resp.json()
    for item in data:
        prediction_enum, created = PredictionEnum.objects.get_or_create(
            id=item['id'],
            name=item['key'],
            defaults={'value': item['id']}
        )


def get_prediction_enum_obj(id):
    try:
        return PredictionEnum.objects.get(id=id)
    except PredictionEnum.DoesNotExist:
        # Save new enums
        save_virtual_framework_tags()
        return PredictionEnum.objects.get(id=id)


class ModelPredictionCallbackSerializer(serializers.Serializer):
    entry_id = serializers.IntegerField()
    predictions = serializers.DictField(child=serializers.DictField())
    thresholds = serializers.DictField(child=serializers.DictField())
    versions = serializers.DictField()

    def create(self, validated_data):
        predictions = validated_data.pop('predictions', {})
        thresholds = validated_data.pop('thresholds', {})
        versions = validated_data.pop('versions')
        model_predictions = []
        entry_id = validated_data["entry_id"]
        if ModelPrediction.objects.filter(entry__id=entry_id).exists():
            return True
        try:
            for category_key, category_value in predictions.items():
                data = {}
                data["entry"] = Entry.objects.get(id=entry_id)
                data["category"] = get_prediction_enum_obj(category_key)
                for key, value in category_value.items():
                    data["tag"] = get_prediction_enum_obj(key)
                    data["prediction"] = value
                    data["threshold"] = thresholds[category_key][key]
                    data['version'] = versions[category_key][key]
                    model_predictions.append(ModelPrediction(**data))
            ModelPrediction.objects.bulk_create(model_predictions)
            return True
        except Exception:
            return serializers.ValidationError("Sth wrong in callback")
