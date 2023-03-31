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


class LeadExtractCallbackView(BaseCallbackView):
    serializer = LeadExtractCallbackSerializer


class UnifiedConnectorLeadExtractCallbackView(BaseCallbackView):
    serializer = UnifiedConnectorLeadExtractCallbackSerializer
