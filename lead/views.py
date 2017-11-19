from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from rest_framework import (
    exceptions,
    filters,
    permissions,
    viewsets,
)
from rest_framework.response import Response
from rest_framework.views import APIView
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from project.models import Project
from lead.models import Lead
from lead.serializers import LeadSerializer

from .tasks import extract_from_lead


class LeadFilterSet(UserResourceFilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """
    published_on__lte = django_filters.DateFilter(
        name='published_on', lookup_expr='lte',
    )
    published_on__gte = django_filters.DateFilter(
        name='published_on', lookup_expr='gte',
    )

    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    confidentiality = django_filters.MultipleChoiceFilter(
        choices=Lead.CONFIDENTIALITIES,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Lead.STATUSES,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    assignee = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = Lead
        fields = ['id', 'title',
                  'text', 'url', 'website']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class LeadViewSet(viewsets.ModelViewSet):
    """
    Lead View
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = LeadFilterSet
    search_fields = ('title', 'source', 'text', 'url', 'website')
    # ordering_fields = omitted to allow ordering by all read-only fields

    def get_queryset(self):
        leads = Lead.get_for(self.request.user)

        lead_id = self.request.GET.get('similar')
        if lead_id:
            similar_lead = Lead.objects.get(id=lead_id)
            leads = leads.filter(project=similar_lead.project).annotate(
                similarity=TrigramSimilarity('title', similar_lead.title)
            ).filter(similarity__gt=0.3).order_by('-similarity')

        return leads


class LeadOptionsView(APIView):
    """
    Options for various attributes related to lead
    """
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

        if (fields is None or 'assignee' in fields):
            assignee = User.objects.filter(
                project__in=projects,
            )
            options['assignee'] = [
                {
                    'key': user.id,
                    'value': user.profile.get_display_name(),
                } for user in assignee.distinct()
            ]

        if (fields is None or 'confidentiality' in fields):
            confidentiality = [
                {
                    'key': c[0],
                    'value': c[1],
                } for c in Lead.CONFIDENTIALITIES
            ]
            options['confidentiality'] = confidentiality

        if (fields is None or 'status' in fields):
            status = [
                {
                    'key': s[0],
                    'value': s[1],
                } for s in Lead.STATUSES
            ]
            options['status'] = status

        if (fields is None or 'project' in fields):
            projects = Project.get_for(request.user)
            options['project'] = [
                {
                    'key': project.id,
                    'value': project.title,
                } for project in projects.distinct()
            ]

        return Response(options)


class LeadExtractionTriggerView(APIView):
    """
    A trigger for extracting lead to generate previews
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lead_id, version=None):
        if not Lead.objects.filter(id=lead_id).exists():
            raise exceptions.NotFound()

        if not Lead.objects.get(id=lead_id).can_modify(request.user):
            raise exceptions.PermissionDenied()

        if not settings.TESTING:
            extract_from_lead.delay(lead_id)

        return Response({
            'extraction_triggered': lead_id,
        })
