from django.db import models
from django.contrib.auth.models import User
from rest_framework import (
    filters,
    permissions,
    response,
    views,
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
                       filters.OrderingFilter, filters.SearchFilter)
    filter_class = AssessmentFilterSet
    search_fields = ('lead__title',)

    def get_queryset(self):
        return Assessment.get_for(self.request.user)


class AssessmentOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        project_query = request.GET.get('project')
        fields_query = request.GET.get('fields')

        projects = Project.get_for(request.user)
        if project_query:
            projects = projects.filter(id__in=project_query.split(','))

        fields = None
        if fields_query:
            fields = fields_query.split(',')

        options = {}

        def _filter_by_projects(qs, projects):
            for p in projects:
                qs = qs.filter(project=p)
            return qs

        if (fields is None or 'created_by' in fields):
            created_by = _filter_by_projects(User.objects, projects)
            options['created_by'] = [
                {
                    'key': user.id,
                    'value': user.profile.get_display_name(),
                } for user in created_by.distinct()
            ]

        if (fields is None or 'project' in fields):
            projects = Project.get_for(request.user)
            options['project'] = [
                {
                    'key': project.id,
                    'value': project.title,
                } for project in projects.distinct()
            ]

        return response.Response(options)


class AssessmentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssessmentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AssessmentTemplate.get_for(self.request.user)
