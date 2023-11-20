from typing import Type
from rest_framework import (
    views,
    permissions,
    response,
    status,
    serializers,
)

from .serializers import (
    AssistedTaggingDraftEntryPredictionCallbackSerializer,
    LeadExtractCallbackSerializer,
    UnifiedConnectorLeadExtractCallbackSerializer,
    AnalysisTopicModelCallbackSerializer,
    AnalysisAutomaticSummaryCallbackSerializer,
    AnalyticalStatementNGramCallbackSerializer,
    AnalyticalStatementGeoCallbackSerializer,
    AutoAssistedTaggingDraftEntryCallbackSerializer
)

from utils.request import RequestHelper


class BaseCallbackView(views.APIView):
    serializer: Type[serializers.Serializer]
    permission_classes = [permissions.AllowAny]

    def post(self, request, **_):
        serializer = self.serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)


class AssistedTaggingDraftEntryPredictionCallbackView(BaseCallbackView):
    serializer = AssistedTaggingDraftEntryPredictionCallbackSerializer


class AutoTaggingDraftEntryPredictionCallbackView(views.APIView):
    serializer = AutoAssistedTaggingDraftEntryCallbackSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, **_):
        data = RequestHelper(url=request.data['entry_extraction_classification_path'], ignore_error=True).json()
        serializer = self.serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)


class LeadExtractCallbackView(BaseCallbackView):
    serializer = LeadExtractCallbackSerializer


class UnifiedConnectorLeadExtractCallbackView(BaseCallbackView):
    serializer = UnifiedConnectorLeadExtractCallbackSerializer


# Analysis
class AnalysisTopicModelCallbackView(BaseCallbackView):
    serializer = AnalysisTopicModelCallbackSerializer


class AnalysisAutomaticSummaryCallbackView(BaseCallbackView):
    serializer = AnalysisAutomaticSummaryCallbackSerializer


class AnalyticalStatementNGramCallbackView(BaseCallbackView):
    serializer = AnalyticalStatementNGramCallbackSerializer


class AnalyticalStatementGeoCallbackView(BaseCallbackView):
    serializer = AnalyticalStatementGeoCallbackSerializer
