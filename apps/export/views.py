from django.conf import settings
from django.db import transaction
from rest_framework import (
    permissions,
    response,
    views,
    viewsets,
    status,
)

from export.serializers import ExportSerializer
from export.models import Export
from project.models import Project
from project.permissions import PROJECT_PERMISSIONS

from export.tasks import export_task


class MetaExtractionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id=None, version=None):
        pass


class ExportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        exports = Export.get_for(self.request.user)

        project = self.request.GET.get('project')
        if project:
            exports = exports.filter(project__id=project)

        is_preview = self.request.GET.get('is_preview')
        if is_preview:
            exports = exports.filter(is_preview=(int(is_preview) == 1))

        return exports


class ExportTriggerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        filters = request.data.get('filters', [])
        filters = {f[0]: f[1] for f in filters}

        project_id = filters.get('project')
        export_type = filters.get('export_type', 'excel')
        export_item = filters.get('export_item', 'entry')

        is_preview = filters.get('is_preview', False)

        if project_id:
            project = Project.objects.get(id=project_id)
        else:
            project = None

        if export_item == 'entry':
            type = Export.ENTRIES
        elif export_item == 'assessment':
            type = Export.ASSESSMENTS
        else:
            return response.Response(
                {'export_item': 'Invalid export item name'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if project:
            # Check permission
            create_permission = PROJECT_PERMISSIONS.export.create
            create_only_unprotected_permission = PROJECT_PERMISSIONS.export.create_only_unprotected

            role = project.get_role(request.user)

            can_create = role.export_permissions & create_permission
            can_create_unprotected = role.export_permissions & create_only_unprotected_permission

            if not can_create and not can_create_unprotected:
                return response.Response({}, status=status.HTTP_403_FORBIDDEN)

        export = Export.objects.create(
            title='Generating Export.....',
            exported_by=request.user,
            pending=True,
            project=project,
            type=type,
            export_type=export_type,
            is_preview=is_preview,
            filters=filters,
        )

        if not settings.TESTING:
            transaction.on_commit(lambda: export_task.delay(export.id))

        return response.Response({
            'export_triggered': export.id,
        })
