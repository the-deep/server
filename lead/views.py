from django.contrib.auth.models import User
from django.db import models
from rest_framework import viewsets, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from project.models import Project
from lead.models import Lead
from lead.serializers import LeadSerializer


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
        return Lead.get_for(self.request.user)


class LeadFilterOptionsView(APIView):
    """
    Filter options for various filters available for leads
    """
    def get(self, request, version=None):
        project_query = request.GET.get('project')
        projects = None
        if project_query:
            projects = project_query.split(',')

        assigned_to = User.objects.filter(
            lead__isnull=False,
        )
        if projects:
            assigned_to = assigned_to.filter(lead__project__in=projects)

        assigned_to = [
            {
                'key': user.id,
                'value': user.profile.get_display_name(),
            } for user in assigned_to.distinct()
        ]

        confidentiality = [
            {
                'key': c[0],
                'value': c[1],
            } for c in Lead.CONFIDENTIALITIES
        ]

        status = [
            {
                'key': s[0],
                'value': s[1],
            } for s in Lead.STATUSES
        ]

        filter_options = {
            'assigned_to': assigned_to,
            'confidentiality': confidentiality,
            'status': status,
        }

        return Response(filter_options)
