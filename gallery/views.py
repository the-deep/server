from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import File
from .serializers import (
    FileSerializer,
)


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return File.get_for(self.request.user)
