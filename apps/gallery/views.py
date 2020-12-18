import logging
from django.urls import reverse
from django.core.cache import cache
from django.views.generic import View
from django.conf import settings
from django.db import models, transaction
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect, get_object_or_404

from rest_framework import (
    views,
    viewsets,
    permissions,
    response,
    filters,
    mixins,
    exceptions,
    decorators,
    status,
)
import django_filters

from deep.permissions import ModifyPermission
from deep.serializers import URLCachedFileField
from project.models import Project
from lead.models import Lead
from entry.models import Entry
from user_resource.filters import UserResourceFilterSet

from utils.extractor.formats import (
    xlsx,
    ods,
)
from .serializers import (
    FileSerializer,
    GoogleDriveFileSerializer,
    DropboxFileSerializer,
    FilePreviewSerializer
)
from .tasks import extract_from_file
from .models import File, FilePreview

logger = logging.getLogger(__name__)


META_EXTRACTION_FUNCTIONS = {  # The functions take file as argument
    'xlsx': xlsx.extract_meta,
    'ods': ods.extract_meta,
}


def DEFAULT_EXTRACTION_FUNCTION(file):
    return {}


class FileView(View):
    def get(self, request, file_id):
        file = get_object_or_404(File, id=file_id)
        return redirect(request.build_absolute_uri(file.file.url))


class PrivateFileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid=None, filename=None):
        queryset = File.objects.prefetch_related('lead_set')
        file = get_object_or_404(queryset, uuid=uuid)
        user = request.user
        leads_pk = file.lead_set.values_list('pk', flat=True)

        if (
                file.is_public or
                Lead.get_for(user).filter(pk__in=leads_pk).exists() or
                Entry.get_for(user).filter(
                    image=request.build_absolute_uri(
                        reverse('file', kwargs={'file_id': file.pk}),
                    )
                ).exists()
                # TODO: Add Profile
        ):
            return redirect(request.build_absolute_uri(file.file.url))
        return response.Response({
            'error': 'Access Forbidden, Contact Admin',
        }, status=status.HTTP_403_FORBIDDEN)


class PublicFileView(View):
    """
    NOTE: Public File API is deprecated.
    """
    def get(self, request, fidb64=None, token=None, filename=None):
        file_id = force_text(urlsafe_base64_decode(fidb64))
        file = get_object_or_404(File, id=file_id)
        return redirect(
            request.build_absolute_uri(
                reverse(
                    'gallery_private_url',
                    kwargs={
                        'uuid': file.uuid, 'filename': filename,
                    },
                )
            )
        )


def filter_files_by_projects(qs, name, value):
    if len(value) == 0:
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
        field_name='projects',
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
    filterset_class = FileFilterSet
    search_fields = ('title', 'file')

    def get_queryset(self):
        if self.action == 'list':
            return File.objects.filter(
                models.Q(created_by=self.request.user) |
                models.Q(is_public=True)
            ).distinct()
        return File.get_for(self.request.user)

    @decorators.action(
        detail=True,
        url_path='preview',
    )
    def get_preview(self, request, pk=None, version=None):
        obj = self.get_object()
        url = self.get_serializer(obj).data.get('file')
        response = redirect(request.build_absolute_uri(url))
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
            extracted=False,
        )

        if not settings.TESTING:
            transaction.on_commit(
                lambda: extract_from_file.delay(file_preview.id)
            )

        return response.Response({
            'extraction_triggered': file_preview.id,
        })


class MetaExtractionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id=None, version=None):
        file_type = request.query_params.get('file_type')

        if file_type is None:
            raise exceptions.ValidationError({
                'file_type': 'file_type should be present'
            })

        file = File.objects.filter(id=file_id).first()
        if file is None:
            raise exceptions.NotFound()

        extraction_function = META_EXTRACTION_FUNCTIONS.get(
            file_type, DEFAULT_EXTRACTION_FUNCTION,
        )

        try:
            return response.Response(extraction_function(file.file))
        except Exception:
            logger.warning('Exception while extracting file {}'.format(file.id))
            raise exceptions.ValidationError('Can\'t get metadata. Check if the file has correct format.')
