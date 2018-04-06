from rest_framework import (
    viewsets,
    response,
)
from .serializers import (
    SourceSerializer,
    SourceOptionSerializer,
    SourceDataSerializer,
)
from .sources.store import source_store


class SourceViewSet(viewsets.ViewSet):
    def list(self, request, version=None):
        sources = source_store.values()
        serializer = SourceSerializer(sources, many=True)
        return response.Response(serializer.data)
