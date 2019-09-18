import requests
import re
from functools import reduce

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models, transaction

from rest_framework.decorators import action
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
from lead.models import LeadGroup, Lead, EMMEntity, LeadEMMTrigger
from lead.serializers import (
    LeadGroupSerializer,
    SimpleLeadGroupSerializer,
    LeadSerializer,
    LegacyLeadSerializer,
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

    def get_serializer_class(self):
        if self.kwargs.get('version') == 'v1':
            return LegacyLeadSerializer
        return super().get_serializer_class()

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

    def _get_extra_emm_info(self, qs=None):
        if qs is None:
            qs = self.filter_queryset(self.get_queryset())

        # Aggregate emm data
        emm_entities = EMMEntity.objects.filter(lead__in=qs).values('name').\
            annotate(
                total_count=models.Count('name')
        ).order_by('-total_count').values('name', 'total_count')

        emm_triggers = LeadEMMTrigger.objects.filter(lead__in=qs).values('emm_keyword', 'emm_risk_factor').\
            annotate(
                total_count=models.Sum('count'),
        ).order_by('-total_count').values('emm_keyword', 'emm_risk_factor', 'total_count')

        extra = {}
        extra['emm_entities'] = emm_entities
        extra['emm_triggers'] = emm_triggers
        return extra

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get', 'post'],
        url_path='emm-summary'
    )
    def emm_summary(self, request, version=None):
        emm_info = {}
        if request.method == 'GET':
            emm_info = self._get_extra_emm_info()
        elif request.method == 'POST':
            raw_filter_data = request.data
            filter_data = self._get_processed_filter_data(raw_filter_data)

            qs = LeadFilterSet(data=filter_data, queryset=self.get_queryset()).qs
            emm_info = self._get_extra_emm_info(qs)
        return response.Response(emm_info)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post'],
        serializer_class=LeadSerializer,
        url_path='filter',
    )
    def leads_filter(self, request, version=None):
        raw_filter_data = request.data
        filter_data = self._get_processed_filter_data(raw_filter_data)

        qs = LeadFilterSet(data=filter_data, queryset=self.get_queryset()).qs
        page = self.paginate_queryset(qs)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(qs, many=True)
        response = self.get_paginated_response(serializer.data)

        return response

    def _get_processed_filter_data(self, raw_filter_data):
        """Make json data usable by filterset class.
        This basically processes list query_params and joins them to comma separated string.
        """
        filter_data = {}
        for key, value in raw_filter_data.items():
            if value and isinstance(value, list):
                filter_data[key] = ','.join([str(x) for x in value])
            else:
                filter_data[key] = value
        return filter_data


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

    # LEGACY SUPPORT
    def get(self, request, version=None):
        project_query = request.GET.get('projects')
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

        def _filter_by_projects_and_groups(qs, projects):
            def _individual_project_query(project):
                return (
                    models.Q(project=project) |
                    models.Q(usergroup__in=project.user_groups.all())
                )

            query = reduce(
                lambda acc, q: acc & q,
                [_individual_project_query(p) for p in projects]
            )
            return qs.filter(query)

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
            projects = Project.get_for_member(request.user)
            options['project'] = [
                {
                    'key': project.id,
                    'value': project.title,
                } for project in projects.distinct()
            ]

        # Create Emm specific options
        options['emm_entities'] = EMMEntity.objects.filter(
            lead__project__in=projects
        ).distinct().values('name').annotate(
            total_count=models.Count('lead'),
            label=models.F('name'),
            key=models.F('id'),
        ).values('key', 'label', 'total_count').order_by('name')

        options['emm_keywords'] = LeadEMMTrigger.objects.filter(
            lead__project__in=projects
        ).values('emm_keyword').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_keyword'),
            label=models.F('emm_keyword')
        ).order_by('emm_keyword')

        options['emm_risk_factors'] = LeadEMMTrigger.objects.filter(
            lead__project__in=projects
        ).values('emm_risk_factor').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_risk_factor'),
            label=models.F('emm_risk_factor'),
        ).order_by('emm_risk_factor')

        # Add info about if the project has emm leads, just check if entities or keywords present
        options['has_emm_leads'] = (not not options['emm_entities']) or (not not options['emm_keywords'])

        return response.Response(options)

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

        # Create Emm specific options
        options['emm_entities'] = fields.get('emm_entities', []) and EMMEntity.objects.filter(
            lead__project__in=projects,
            name__in=fields['emm_entities'],
        ).distinct().values('name').annotate(
            total_count=models.Count('lead'),
            label=models.F('name'),
            key=models.F('id'),
        ).values('key', 'label', 'total_count').order_by('name')

        options['emm_keywords'] = fields.get('emm_keywords', []) and LeadEMMTrigger.objects.filter(
            emm_keyword__in=fields['emm_keywords'],
            lead__project__in=projects
        ).values('emm_keyword').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_keyword'),
            label=models.F('emm_keyword')
        ).order_by('emm_keyword')

        options['emm_risk_factors'] = fields.get('emm_risk_factors', []) and LeadEMMTrigger.objects.filter(
            emm_risk_factor__in=fields['emm_risk_factors'],
            lead__project__in=projects,
        ).values('emm_risk_factor').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_risk_factor'),
            label=models.F('emm_risk_factor'),
        ).order_by('emm_risk_factor')

        options['has_emm_leads'] = EMMEntity.objects.filter(lead__project__in=projects).exists() or \
            LeadEMMTrigger.objects.filter(lead__project__in=projects).exists()

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
            models.Q(short_name__iexact=title) |
            models.Q(long_name__iexact=title)
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

        # LEGACY
        organization_context = {
            'source': source_raw,
            'author': author_raw,
        }
        if version != 'v1':
            organization_context = {
                'source': self.get_organization(source_raw),
                'author': self.get_organization(author_raw),
                'source_raw': source_raw,
                'author_raw': author_raw,
            }

        context = {
            **organization_context,
            'project': project and project.id,
            'title': title,
            'date': date,
            'country': country,
            'website': website,
            'url': url,
            'existing': check_if_url_exists(url, request.user, project),
        }

        return response.Response(context)


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
