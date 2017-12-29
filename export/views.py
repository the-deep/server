from django.conf import settings
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
        return Export.get_for(self.request.user)


class ExportTriggerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        filters = request.data.get('filters', [])
        filters = {f[0]: f[1] for f in filters}

        project_id = request.data.get('project')
        export_type = request.data.get('export_type', 'excel')

        export = Export.objects.create(
            title='tmp',
            exported_by=request.user,
            pending=True,
        )

        if not settings.TESTING:
            export_entries.delay(
                export_type,
                export.id,
                request.user.id,
                project_id,
                filters,
            )

        return response.Response({
            'export_triggered': export.id,
        })
