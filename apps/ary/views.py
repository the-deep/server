import copy
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

from deep.permissions import ModifyPermission, CreateAssessmentPermission
from project.models import Project
from project.permissions import PROJECT_PERMISSIONS as PROJ_PERMS
from lead.views import BaseCopyView, LeadCopyView

from .filters import AssessmentFilterSet, PlannedAssessmentFilterSet
from .models import (
    Assessment,
    PlannedAssessment,
    AssessmentTemplate,
)
from .serializers import (
    AssessmentSerializer,
    PlannedAssessmentSerializer,
    AssessmentTemplateSerializer,
    LeadAssessmentSerializer,
    LeadGroupAssessmentSerializer,
)


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, CreateAssessmentPermission,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter, filters.SearchFilter)
    filterset_class = AssessmentFilterSet
    ordering_fields = ('lead__title', 'created_by', 'created_at')
    search_fields = ('lead__title',)

    def get_queryset(self):
        return Assessment.get_for(self.request.user)


class PlannedAssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, CreateAssessmentPermission,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter, filters.SearchFilter)
    filterset_class = PlannedAssessmentFilterSet
    ordering_fields = ('title', 'created_by', 'created_at')
    search_fields = ('title',)

    def get_queryset(self):
        return PlannedAssessment.get_for(self.request.user)


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


class AssessmentCopyView(BaseCopyView):
    """
    Copy assesment to another project
    """

    CLONE_PERMISSION = PROJ_PERMS.assessment
    CLONE_ROLE = 'role__assessment_permissions'
    CLONE_ENTITY_NAME = 'assessment'
    CLONE_ENTITY = Assessment

    def get_clone_context(self, request):
        return {
            'lead_create_access_project_ids': set(LeadCopyView.get_project_ids_with_create_access(request))
        }

    @classmethod
    def clone_entity(cls, original_ary, project_id, user, context):
        lead, is_new = LeadCopyView.clone_or_get_lead(
            original_ary.lead, project_id, user, context,
            context['lead_create_access_project_ids'],
        )
        # Skip assessment creation if lead already has a assessment (or use lead.refresh_from_db())
        if lead is None or (not is_new and getattr(lead, 'assessment', None)):
            return

        ary = copy.deepcopy(original_ary)

        # LeadGroup?
        ary.pk = None
        ary.project_id = project_id
        ary.lead = lead
        ary.save()

        return ary
