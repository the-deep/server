from rest_framework import viewsets, response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from django.conf import settings
import requests
import json
from nlp.serializers import (
    ModelInfoSerializer,
    ModelPredictionSerializer,
    ReviewTagSerializer,
    ModelPredictionRequestSerializer,
    ModelPredictionCallbackSerializer,
)
from nlp.models import ModelInfo, ModelPrediction, ReviewTag
from entry.models import Entry


class ModelInfoViewSet(viewsets.ModelViewSet):
    serializer_class = ModelInfoSerializer

    def get_queryset(self):
        return ModelInfo.objects.all()


class ModelPredictionViewSet(viewsets.ModelViewSet):
    serializer_class = ModelPredictionSerializer
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    def get_queryset(self):
        return ModelPrediction.objects.all()

    @action(
        detail=False,
        methods=['post'],
        serializer_class=ModelPredictionRequestSerializer,
        url_path='model-predict'
    )
    def model_predict(self, request, version=None):
        serializer = ModelPredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry_ids = serializer.data.get("entry_ids", [])
        entries = Entry.objects.filter(id__in=entry_ids)
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            'entries': [],
            'callback_url': settings.MODEL_PREDICTION_CALLBACK_URL
        }
        for entry in entries:
            payload["entries"].append({'entry_id': entry.id, "entry": entry.excerpt})
        if not payload["entries"]:
            return response.Response("Entries not selected")
        nlp_response = requests.post(f"{settings.EXTRACTOR_URL}/entry_predict", headers=headers, data=json.dumps(payload))
        if nlp_response.status_code == 200:
            return response.Response({'Prediction request sent'})
        return response.Response({'Prediction request failed'})

    @action(
        detail=False,
        methods=['post'],
        serializer_class=ModelPredictionCallbackSerializer,
        url_path='model-predict-callback',
    )
    def model_predict_callback(self, request, version=None):
        serializer = ModelPredictionCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"Prediction callback handled"})


class ReviewTagViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewTagSerializer

    def get_queryset(self):
        return ReviewTag.objects.all()
