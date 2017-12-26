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
from .models import CategoryEditor
from .serializers import CategoryEditorSerializer


class CategoryEditorViewSet(viewsets.ModelViewSet):
    serializer_class = CategoryEditorSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return CategoryEditor.get_for(self.request.user)


class CategoryEditorCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ce_id, version=None):
        if not CategoryEditor.objects.filter(
            id=ce_id
        ).exists():
            raise exceptions.NotFound()

        category_editor = CategoryEditor.objects.get(
            id=ce_id
        )
        if not category_editor.can_get(request.user):
            raise exceptions.PermissionDenied()

        new_ce = category_editor.clone(request.user)
        serializer = CategoryEditorSerializer(
            new_ce,
            context={'request': request},
        )

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            project.category_editor = new_ce
            project.modified_by = request.user
            project.save()

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )
