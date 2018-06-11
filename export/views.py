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

from export.tasks import export_entries, export_assessment

import logging
logger = logging.getLogger('django')


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
            export_task = export_entries
            type = Export.ENTRIES
        elif export_item == 'assessment':
            export_task = export_assessment
            type = Export.ASSESSMENTS
        else:
            return response.Response(
                {'export_item': 'Invalid export item name'},
                status=status.HTTP_400_BAD_REQUEST
            )

        export = Export.objects.create(
            title='tmp',
            exported_by=request.user,
            pending=True,
            project=project,
            type=type,
            is_preview=is_preview,
        )

        if not settings.TESTING:
            transaction.on_commit(lambda: export_task.delay(
                export_type,
                export.id,
                request.user.id,
                project_id,
                filters,
            ))

        return response.Response({
            'export_triggered': export.id,
        })
