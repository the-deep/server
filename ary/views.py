from django.db import models
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import (
    filters,
    mixins,
    permissions,
    response,
    views,
    viewsets,
)
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet
from project.models import Project
from lead.models import Lead, LeadGroup

from .models import (
    Assessment,
    AssessmentTemplate,
)
from .serializers import (
    AssessmentSerializer,
    AssessmentTemplateSerializer,
    LeadAssessmentSerializer,
    LeadGroupAssessmentSerializer,
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
    lead_group = django_filters.ModelMultipleChoiceFilter(
        queryset=LeadGroup.objects.all(),
        lookup_expr='in',
    )
    created_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = Assessment
        fields = ['id', 'lead__title', 'lead_group__title']

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
    ordering_fields = ('lead__title', 'created_by', 'created_at')
    search_fields = ('lead__title',)

    def get_queryset(self):
        return Assessment.get_for(self.request.user)


class LeadAssessmentViewSet(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """
    Assessments accessed using associated lead id.

    Only allow, put, patch, and get requests as this api
    is accessed through lead.
    In put requests, if there is no existing assessment, one is
    automatically created.
    """
    serializer_class = LeadAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    lookup_field = 'lead'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Assessment.get_for(self.request.user)

    def update(self, request, *args, **kwargs):
        # For put/patch request, we want to set `lead` data
        # from url
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        data = {
            **request.data,
            'lead': kwargs['pk'],
        }
        serializer = self.get_serializer(instance, data=data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return response.Response(serializer.data)


class LeadGroupAssessmentViewSet(mixins.RetrieveModelMixin,
                                 mixins.UpdateModelMixin,
                                 mixins.DestroyModelMixin,
                                 viewsets.GenericViewSet):
    """
    Assessments accessed using associated lead group id.

    Only allow, put, patch, and get requests as this api
    is accessed through lead.
    In put requests, if there is no existing assessment, one is
    automatically created.
    """
    serializer_class = LeadGroupAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    lookup_field = 'lead_group'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Assessment.get_for(self.request.user)

    def update(self, request, *args, **kwargs):
        # For put/patch request, we want to set `lead_group` data
        # from url
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Http404:
            instance = None

        data = {
            **request.data,
            'lead_group': kwargs['pk'],
        }
        serializer = self.get_serializer(instance, data=data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return response.Response(serializer.data)


class AssessmentOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        project_query = request.GET.get('project')
        fields_query = request.GET.get('fields')

        projects = Project.get_for_member(request.user)
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
            projects = Project.get_for_member(request.user)
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
