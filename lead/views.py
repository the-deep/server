import requests
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models, transaction
from rest_framework import (
    exceptions,
    filters,
    permissions,
    response,
    status,
    views,
    viewsets,
)
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from project.models import Project
from lead.models import LeadGroup, Lead
from lead.serializers import (
    LeadGroupSerializer,
    LeadSerializer,
    LeadPreviewSerializer,
)

from lead.tasks import extract_from_lead
from utils.web_info_extractor import WebInfoExtractor
from utils.common import USER_AGENT

headers = {
    'User-Agent': USER_AGENT
}

valid_lead_url_regex = re.compile(
    # http:// or https://
    r'^(?:http)s?://'
    # domain...
    r'(?:(?:[A-Z0-9]'
    r'(?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
    r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    # localhost...
    r'localhost|'
    # ...or ip
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    # optional port
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class LeadGroupFilterSet(UserResourceFilterSet):
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = LeadGroup
        fields = ['id', 'title']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class LeadGroupViewSet(viewsets.ModelViewSet):
    serializer_class = LeadGroupSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_class = LeadGroupFilterSet

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        return LeadGroup.get_for(user)


class LeadFilterSet(UserResourceFilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """
    published_on__lt = django_filters.DateFilter(
        name='published_on', lookup_expr='lte',
    )
    published_on__gt = django_filters.DateFilter(
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
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = LeadFilterSet
    search_fields = ('title', 'source', 'text', 'url', 'website')
    # ordering_fields = omitted to allow ordering by all read-only fields

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        project_list = data and data.get('project')

        if project_list and isinstance(project_list, list):
            kwargs.pop('data')
            kwargs.pop('many', None)
            data.pop('project')

            data_list = []
            for project in project_list:
                data_list.append({
                    **data,
                    'project': project,
                })

            return super(LeadViewSet, self).get_serializer(
                data=data_list,
                many=True,
                *args,
                **kwargs,
            )

        return super(LeadViewSet, self).get_serializer(
            *args,
            **kwargs,
        )

    def get_queryset(self):
        leads = Lead.get_for(self.request.user)

        lead_id = self.request.GET.get('similar')
        if lead_id:
            similar_lead = Lead.objects.get(id=lead_id)
            leads = leads.filter(project=similar_lead.project).annotate(
                similarity=TrigramSimilarity('title', similar_lead.title)
            ).filter(similarity__gt=0.3).order_by('-similarity')
        return leads


class LeadPreviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeadPreviewSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Lead.get_for(self.request.user)


class LeadOptionsView(views.APIView):
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

        def _filter_by_projects(qs, projects):
            for p in projects:
                qs = qs.filter(project=p)
            return qs

        def _filter_by_projects_and_groups(qs, projects):
            for p in projects:
                qs = qs.filter(
                    models.Q(project=p) |
                    models.Q(usergroup__in=p.user_groups.all())
                )
            return qs

        if (fields is None or 'lead_group' in fields):
            lead_groups = _filter_by_projects(
                LeadGroup.objects,
                projects,
            )
            options['lead_group'] = [
                {
                    'key': group.id,
                    'value': group.title,
                } for group in lead_groups.distinct()
            ]

        if (fields is None or 'assignee' in fields):
            assignee = _filter_by_projects_and_groups(User.objects, projects)
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

        return response.Response(options)


class LeadExtractionTriggerView(views.APIView):
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
            transaction.on_commit(lambda: extract_from_lead.delay(lead_id))

        return response.Response({
            'extraction_triggered': lead_id,
        })


class LeadWebsiteFetch(views.APIView):
    """
    Get Information about the website
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        return self.website_fetch(url)

    def get(self, request, *args, **kwargs):
        url = request.query_params.get('url')
        response = self.website_fetch(url)
        response['Cache-Control'] = 'max-age={}'.format(60 * 60)
        return response

    def website_fetch(self, url):
        https_url = url
        http_url = url

        if not valid_lead_url_regex.match(url):
            return response.Response({
                'error': 'Url is not valid'
            }, status=status.HTTP_400_BAD_REQUEST)

        if url.find('http://') >= 0:
            https_url = url.replace('http://', 'https://', 1)
        else:
            http_url = url.replace('https://', 'http://', 1)

        try:
            # Try with https
            r = requests.head(
                https_url, headers=headers,
                timeout=settings.LEAD_WEBSITE_FETCH_TIMEOUT
            )
        except requests.exceptions.RequestException:
            https_url = None
            # Try with http
            try:
                r = requests.head(
                    http_url, headers=headers,
                    timeout=settings.LEAD_WEBSITE_FETCH_TIMEOUT
                )
            except requests.exceptions.RequestException:
                # doesn't work
                return response.Response({
                    'error': 'can\'t fetch url'
                })

        return response.Response({
            'headers': r.headers,
            'httpsUrl': https_url,
            'httpUrl': http_url
        })


class WebInfoExtractView(views.APIView):
    """
    Extract information from a website for new lead
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        url = request.data.get('url')

        extractor = WebInfoExtractor(url)
        date = extractor.get_date()
        country = extractor.get_country()
        source = extractor.get_source()
        website = extractor.get_website()
        title = extractor.get_title()

        project = None
        if country:
            project = Project.get_for(request.user).filter(
                regions__title__icontains=country
            ).first()

        project = project or request.user.profile.last_active_project

        return response.Response({
            'project': project and project.id,
            'title': title,
            'date': date,
            'country': country,
            'website': website,
            'url': url,
            'source': source,
        })
