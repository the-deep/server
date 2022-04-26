from django.db import transaction
from rest_framework import (
    views,
    permissions,
    response,
    status,
)

from .serializers import AssistedTaggingDraftEntryPredictionCallbackSerializer


class AssistedTaggingDraftEntryPredictionCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):
        serializer = AssistedTaggingDraftEntryPredictionCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)
