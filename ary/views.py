from rest_framework import (
    permissions,
    viewsets,
)
from deep.permissions import ModifyPermission

from .models import (
    Assessment,
    AssessmentTemplate,
)
from .serializers import (
    AssessmentSerializer,
    AssessmentTemplateSerializer,
)


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Assessment.get_for(self.request.user)


class AssessmentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssessmentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AssessmentTemplate.get_for(self.request.user)
