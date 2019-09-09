import requests
from django.utils import timezone
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models, transaction
from rest_framework import (
    serializers,
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
from deep.paginations import AutocompleteSetPagination

from lead.filter_set import (
    LeadGroupFilterSet,
    LeadFilterSet,
)
from project.models import Project, ProjectMembership
from project.permissions import PROJECT_PERMISSIONS as PROJ_PERMS
from project.serializers import SimpleProjectSerializer
from user.serializers import SimpleUserSerializer
from organization.models import Organization
from organization.serializers import SimpleOrganizationSerializer
from lead.models import LeadGroup, Lead
from lead.serializers import (
    LeadGroupSerializer,
    SimpleLeadGroupSerializer,
    LeadSerializer,
    LeadPreviewSerializer,
    check_if_url_exists,
)

from lead.tasks import extract_from_lead
from utils.web_info_extractor import get_web_info_extractor
from utils.common import DEFAULT_HEADERS


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


class LeadGroupViewSet(viewsets.ModelViewSet):
    serializer_class = LeadGroupSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = LeadGroupFilterSet
    search_fields = ('title',)

    def get_queryset(self):
        return LeadGroup.get_for(self.request.user)


class ProjectLeadGroupViewSet(LeadGroupViewSet):
    """
    NOTE: Only to be used by Project's action route [DONOT USE DIRECTLY]
    """
    pagination_class = AutocompleteSetPagination
    serializer_class = SimpleLeadGroupSerializer
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        project = Project.objects.get(pk=self.request.query_params['project'])
        return LeadGroup.get_for_project(project)


class LeadViewSet(viewsets.ModelViewSet):
    """
    Lead View
    """
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = LeadFilterSet
    search_fields = ('title', 'source', 'text', 'url', 'website')
    # ordering_fields = omitted to allow ordering by all read-only fields

    def filter_queryset(self, queryset):
        # For some reason, the ordering is not working for `assignee` field
        # so, force ordering with anything passed in the query param
        qs = super().filter_queryset(queryset)
        ordering = self.request.query_params.get('ordering', '')
        orderings = [x for x in ordering.split(',') if x]

        for ordering in orderings:
            if ordering == '-page_count':
                qs = qs.order_by(models.F('leadpreview__page_count').desc(nulls_last=True))
            elif ordering == 'page_count':
                qs = qs.order_by(models.F('leadpreview__page_count').asc(nulls_first=True))
            else:
                qs = qs.order_by(ordering)

        return qs

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

            return super().get_serializer(
                data=data_list,
                many=True,
                *args,
                **kwargs,
            )

        return super().get_serializer(
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

    Example:
    ```json
    {
        "projects": [1, 2],
        "leadGroups": [1, 2],
        "members": [1, 2],
        "organizations": [1, 2]
    }
    ```
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        fields = request.data
        projects_id = fields.get('projects', [])
        lead_groups_id = fields.get('lead_groups', [])
        organizations_id = fields.get('organizations', [])
        members_id = fields.get('members')

        projects = Project.get_for_member(request.user).filter(
            id__in=projects_id,
        )
        if not projects.exists():
            raise exceptions.NotFound('Provided projects not found')

        def _filter_by_project(qs):
            return qs.filter(project__in=projects).distinct()

        def _filter_by_project_and_group(qs):
            for project in projects:
                qs = qs.filter(
                    models.Q(project=project) |
                    models.Q(usergroup__in=project.user_groups.all())
                )
            return qs.distinct()

        options = {
            'projects': SimpleProjectSerializer(projects, many=True).data,

            # Static Options
            'confidentiality': [
                {
                    'key': c[0],
                    'value': c[1],
                } for c in Lead.CONFIDENTIALITIES
            ],

            'status': [
                {
                    'key': s[0],
                    'value': s[1],
                } for s in Lead.STATUSES
            ],

            # Dynamic Options
            'lead_groups': lead_groups_id and (
                SimpleLeadGroupSerializer(
                    _filter_by_project(
                        LeadGroup.objects.filter(id__in=lead_groups_id),
                    ),
                    many=True,
                ).data
            ),

            'members': SimpleUserSerializer(
                _filter_by_project_and_group(
                    User.objects.filter(id__in=members_id)
                    if members_id is not None else User.objects,
                ),
                many=True,
            ).data,

            'organizations': organizations_id and (
                SimpleOrganizationSerializer(
                    Organization.objects.filter(id__in=organizations_id),
                    many=True,
                ).data
            ),
        }

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
                https_url, headers=DEFAULT_HEADERS,
                timeout=settings.LEAD_WEBSITE_FETCH_TIMEOUT
            )
        except requests.exceptions.RequestException:
            https_url = None
            # Try with http
            try:
                r = requests.head(
                    http_url, headers=DEFAULT_HEADERS,
                    timeout=settings.LEAD_WEBSITE_FETCH_TIMEOUT
                )
            except requests.exceptions.RequestException:
                # doesn't work
                return response.Response(
                    {'error': 'can\'t fetch url'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return response.Response({
            'headers': dict(r.headers),
            'httpsUrl': https_url,
            'httpUrl': http_url,
            'timestamp': timezone.now().timestamp(),
        })


class WebInfoExtractView(views.APIView):
    """
    Extract information from a website for new lead
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_organization(self, title):
        org = Organization.objects.filter(
            models.Q(title__iexact=title) |
            models.Q(short_name__iexact=title)
        ).first()
        if org:
            return SimpleOrganizationSerializer(org).data

    def post(self, request, version=None):
        url = request.data.get('url')

        extractor = get_web_info_extractor(url)
        date = extractor.get_date()
        country = extractor.get_country()
        source_raw = extractor.get_source()
        author_raw = extractor.get_author()
        website = extractor.get_website()
        title = extractor.get_title()

        project = None
        if country:
            project = Project.get_for_member(request.user).filter(
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
            'source': self.get_organization(source_raw),
            'source_raw': source_raw,
            'author': self.get_organization(author_raw),
            'author_raw': author_raw,
            'existing': check_if_url_exists(url, request.user, project),
        })


class LeadCopyView(views.APIView):
    """
    Copy lead to another project
    """
    permission_classes = [permissions.IsAuthenticated]

    def clone_lead(self, lead, project_id, user):
        lead.pk = None
        try:
            LeadSerializer.add_update__validate({
                'project': project_id,
            }, lead, lead.attachment)
        except serializers.ValidationError:
            return  # SKIP COPY if validation fails
        lead.project_id = project_id
        lead.save()
        lead.assignee.add(user)
        return lead

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        project_ids = ProjectMembership.objects.filter(
            member=request.user,
            project_id__in=request.data.get('projects', [])
        ).annotate(
            lead_add_permission=models.F('role__lead_permissions')
            .bitand(PROJ_PERMS.lead.create)
        ).filter(lead_add_permission=PROJ_PERMS.lead.create)\
            .values_list('project_id', flat=True)

        leads = Lead.get_for(request.user).filter(
            pk__in=request.data.get('leads', [])
        )

        processed_lead = []
        processed_lead_by_project = {}
        for lead in leads:
            lead_original_project = lead.project_id
            processed_lead.append(lead.pk)

            edit_or_create_permission = PROJ_PERMS.lead.create | PROJ_PERMS.lead.modify
            edit_or_create_membership = ProjectMembership.objects.filter(
                member=request.user,
                project=lead.project,
            ).annotate(
                clone_perm=models.F('role__lead_permissions')
                .bitand(edit_or_create_permission)
            ).filter(clone_perm__gt=0).first()

            if not edit_or_create_membership:
                raise exceptions.PermissionDenied(
                    'You do not have enough permissions to clone lead from the '
                    f'project {lead.project.title}'
                )

            for project_id in project_ids:
                if project_id == lead_original_project:
                    continue

                # NOTE: To clone Lead to another project
                p_lead = self.clone_lead(lead, project_id, request.user)
                if p_lead:
                    processed_lead_by_project[project_id] = (
                        processed_lead_by_project.get(project_id) or []
                    ) + [p_lead.pk]

        return response.Response({
            'projects': project_ids,
            'leads': processed_lead,
            'leads_by_projects': processed_lead_by_project,
        })
