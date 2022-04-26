from rest_framework import (
    views,
    permissions,
    response,
    status,
)
from .serializers import ExtractCallbackSerializer


class ConnectorLeadExtractCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ExtractCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)
