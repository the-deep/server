from rest_framework import mixins
from deep.permissions import ModifyPermission
from django.conf import settings
from rest_framework import (
    exceptions,
    permissions,
    response,
    views,
    viewsets,
)

from .tasks import extract_from_file
from .models import File, FilePreview
from .serializers import (
    FileSerializer,
    GoogleDriveFileSerializer,
    DropboxFileSerializer,
    FilePreviewSerializer
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


class FilePreviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FilePreviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FilePreview.objects.all()


class FileExtractionTriggerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        file_ids = request.data.getlist('file_ids')
        file_preview = FilePreview.objects.create(
            file_ids=file_ids,
            extracted=False
        )

        if not settings.TESTING:
            extract_from_file(file_preview.id)

        return response.Response({
            'extraction_triggered': file_preview.id,
        })
