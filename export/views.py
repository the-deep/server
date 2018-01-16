from django.conf import settings
from django.db import transaction
from rest_framework import (
    permissions,
    response,
    views,
    viewsets,
)

from export.serializers import ExportSerializer
from export.models import Export

from export.tasks_entries import export_entries


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
            exports = exports.filter(is_preview=True)

        return exports


class ExportTriggerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        filters = request.data.get('filters', [])
        filters = {f[0]: f[1] for f in filters}

        project_id = filters.get('project')
        export_type = filters.get('export_type', 'excel')

        is_preview = filters.get('preview', False)

        export = Export.objects.create(
            title='tmp',
            exported_by=request.user,
            pending=True,
            project=project_id,
            is_preview=is_preview,
        )

        if not settings.TESTING:
            transaction.on_commit(lambda: export_entries.delay(
                export_type,
                export.id,
                request.user.id,
                project_id,
                filters,
            ))

        return response.Response({
            'export_triggered': export.id,
        })
