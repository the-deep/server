from django.db import models
from rest_framework import (
    filters,
    permissions,
    viewsets,
)
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet
from project.models import Project
from lead.models import Lead

from .models import (
    Assessment,
    AssessmentTemplate,
)
from .serializers import (
    AssessmentSerializer,
    AssessmentTemplateSerializer,
)


class AssessmentFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        name='lead__project',
        lookup_expr='in',
    )
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
    )

    class Meta:
        model = Assessment
        fields = ['id', 'lead__title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter)
    filter_class = AssessmentFilterSet

    def get_queryset(self):
        return Assessment.get_for(self.request.user)


class AssessmentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssessmentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AssessmentTemplate.get_for(self.request.user)
