from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework.decorators import action
from rest_framework import (
    permissions,
    response,
    views,
    viewsets,
    status,
)
from celery.task.control import revoke

from export.serializers import ExportSerializer
from export.models import Export
from project.models import Project
from project.permissions import PROJECT_PERMISSIONS
from export.filter_set import (
    ExportFilterSet,
)

from export.tasks import export_task


class MetaExtractionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id=None, version=None):
        pass


class ExportViewSet(viewsets.ModelViewSet):
    serializer_class = ExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ExportFilterSet

    def get_queryset(self):
        qs = Export.get_for(self.request.user)
        if self.action == 'list':
            return qs.filter(is_preview=False)
        return qs

    @action(
        detail=True,
        url_path='cancel',
        methods=('post',),
    )
    def cancel(self, request, pk=None, version=None):
        export = self.get_object()
        if export.status in [Export.PENDING, Export.STARTED]:
            revoke(export.get_task_id(clear=True), terminate=True)
            export.status = Export.CANCELED
        export.save()
        return self.retrieve(request, pk=pk)

    def destroy(self, request, *args, **kwargs):
        export = self.get_object()
        export.is_deleted = True
        export.save()
        return response.Response({}, status=status.HTTP_204_NO_CONTENT)


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
        elif export_item == 'planned_assessment':
            type = Export.PLANNED_ASSESSMENTS
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

        if True or not settings.TESTING:
            transaction.on_commit(
                lambda: export.set_task_id(export_task.delay(export.id).id)
            )

        return response.Response({
            'export_triggered': export.id,
        })
