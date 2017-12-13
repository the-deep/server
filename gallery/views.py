from rest_framework import viewsets, permissions
from rest_framework import mixins
from deep.permissions import ModifyPermission
from django.conf import settings

from .models import File
from .serializers import (
    FileSerializer,
    GoogleDriveFileSerializer,
    DropboxFileSerializer,
)


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return File.get_for(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        response = super(FileViewSet, self).retrieve(request, *args, **kwargs)
        response['Cache-Control'] = 'max-age={}'.format(
            settings.MAX_FILE_CACHE_AGE)
        return response


class GoogleDriveFileViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = GoogleDriveFileSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]


class DropboxFileViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = DropboxFileSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
