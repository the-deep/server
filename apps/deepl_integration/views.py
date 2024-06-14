from typing import Type

from rest_framework import permissions, response, serializers, status, views

from .serializers import (
    AnalysisAutomaticSummaryCallbackSerializer,
    AnalysisTopicModelCallbackSerializer,
    AnalyticalStatementGeoCallbackSerializer,
    AnalyticalStatementNGramCallbackSerializer,
    AssistedTaggingDraftEntryPredictionCallbackSerializer,
    AutoAssistedTaggingDraftEntryCallbackSerializer,
    LeadExtractCallbackSerializer,
    UnifiedConnectorLeadExtractCallbackSerializer,
)


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


class AutoTaggingDraftEntryPredictionCallbackView(BaseCallbackView):
    serializer = AutoAssistedTaggingDraftEntryCallbackSerializer


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
