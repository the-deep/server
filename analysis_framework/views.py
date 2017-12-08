from rest_framework import (
    exceptions,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from deep.permissions import ModifyPermission

from project.models import Project
from .models import (
    AnalysisFramework, Widget, Filter, Exportable
)
from .serializers import (
    AnalysisFrameworkSerializer, WidgetSerializer,
    FilterSerializer, ExportableSerializer
)


class AnalysisFrameworkViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AnalysisFramework.get_for(self.request.user)


class AnalysisFrameworkCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, af_id, version=None):
        if not AnalysisFramework.objects.filter(
            id=af_id
        ).exists():
            raise exceptions.NotFound()

        analysis_framework = AnalysisFramework.objects.get(
            id=af_id
        )
        if not analysis_framework.can_get(request.user):
            raise exceptions.PermissionDenied()

        new_af = analysis_framework.clone(request.user)
        serializer = AnalysisFrameworkSerializer(
            new_af,
            context={'request': request},
        )

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            project.analysis_framework = new_af
            project.modified_by = request.user
            project.save()

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class WidgetViewSet(viewsets.ModelViewSet):
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Widget.get_for(self.request.user)


class FilterViewSet(viewsets.ModelViewSet):
    serializer_class = FilterSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Filter.get_for(self.request.user)


class ExportableViewSet(viewsets.ModelViewSet):
    serializer_class = ExportableSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Exportable.get_for(self.request.user)
