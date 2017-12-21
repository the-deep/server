from rest_framework import (
    permissions,
    viewsets,
)
from deep.permissions import ModifyPermission
from .models import CategoryEditor
from .serializers import CategoryEditorSerializer


class CategoryEditorViewSet(viewsets.ModelViewSet):
    serializer_class = CategoryEditorSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return CategoryEditor.get_for(self.request.user)
