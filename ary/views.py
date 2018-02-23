from rest_framework import (
    permissions,
    viewsets,
)
from deep.permissions import ModifyPermission

from .models import AssessmentTemplate
from .serializers import AssessmentTemplateSerializer


class AssessmentTemplateViewSet(viewsets.ModelViewSet):
    """
    Template view set
    """
    serializer_class = AssessmentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    queryset = AssessmentTemplate.objects.all()
