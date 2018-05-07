from .tasks import extract_from_file
from .models import File, FilePreview
from rest_framework import (
    views,
    viewsets,
    permissions,
    response,
    filters,
    mixins,
)
from deep.permissions import ModifyPermission
from django.conf import settings
from django.db import models, transaction
import django_filters

from project.models import Project
from user_resource.filters import UserResourceFilterSet
from .serializers import (
    FileSerializer,
    GoogleDriveFileSerializer,
    DropboxFileSerializer,
    FilePreviewSerializer
)


def filter_files_by_projects(qs, name, value):
    if value.count() == 0:
        return qs

    return qs.filter(
        models.Q(projects__in=value) |
        models.Q(lead__project__in=value)
    )


class FileFilterSet(UserResourceFilterSet):
    """
    File filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """

    projects = django_filters.ModelMultipleChoiceFilter(
        name='projects',
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
        method=filter_files_by_projects,
    )

    class Meta:
        model = File
        fields = ['id', 'title', 'mime_type']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = FileFilterSet
    search_fields = ('title', 'file')

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
        file_ids = request.data.get('file_ids')

        # Check if preview with same file ids already exists
        existing = FilePreview.objects.filter(
            file_ids__contains=file_ids,
            file_ids__len=len(file_ids),
        ).first()

        # If so, just return that
        if existing:
            return response.Response({
                'extraction_triggered': existing.id,
            })

        file_preview = FilePreview.objects.create(
            file_ids=file_ids,
            extracted=False
        )

        if not settings.TESTING:
            transaction.on_commit(
                lambda: extract_from_file.delay(file_preview.id)
            )

        return response.Response({
            'extraction_triggered': file_preview.id,
        })
