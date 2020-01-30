import requests
import re

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
from drf_yasg.utils import swagger_auto_schema

import django_filters

from deep.permissions import ModifyPermission
from deep.paginations import AutocompleteSetPagination

from lead.filter_set import (
    LeadGroupFilterSet,
    LeadFilterSet,
)
from project.models import Project, ProjectMembership
from project.permissions import PROJECT_PERMISSIONS as PROJ_PERMS
from organization.models import Organization
from organization.serializers import SimpleOrganizationSerializer
from .models import (
    LeadGroup,
    Lead,
    EMMEntity,
    LeadEMMTrigger,
    LeadPreviewImage,
)
from .serializers import (
    LeadGroupSerializer,
    SimpleLeadGroupSerializer,
    LeadSerializer,
    LegacyLeadSerializer,
    LeadPreviewSerializer,
    check_if_url_exists,
    LeadOptionsSerializer,
    LeadOptionsBodySerializer,
    LegacyLeadOptionsSerializer,
)

from lead.tasks import extract_from_lead
from utils.web_info_extractor import get_web_info_extractor
from utils.common import DEFAULT_HEADERS
from connector.sources.base import OrganizationSearch


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


def _filter_users_by_projects_memberships(user_qs, projects):
    # NOTE: No need to filter by usergroups as membership is automatically created
    for project in projects:
        user_qs = user_qs.filter(project=project)
    return user_qs


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
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    # NOTE: Using LeadFilterSet for both search and ordering
    filterset_class = LeadFilterSet

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
            if isinstance(value, list):
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
    """
    permission_classes = [permissions.IsAuthenticated]

    # LEGACY SUPPORT
    @swagger_auto_schema(responses={200: LegacyLeadOptionsSerializer()})
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

        project_filter = models.Q(project__in=projects)

        options['lead_group'] = [
            {
                'key': group.id,
                'value': group.title,
            } for group in LeadGroup.objects.filter(project_filter).distinct()
        ] if (fields is None or 'lead_group' in fields) else []

        options['assignee'] = [
            {
                'key': user.id,
                'value': user.profile.get_display_name(),
            } for user in _filter_users_by_projects_memberships(
                User.objects.all(), projects,
            ).prefetch_related('profile').distinct()
        ] if (fields is None or 'assignee' in fields) else []

        options['confidentiality'] = [
            {
                'key': c[0],
                'value': c[1],
            } for c in Lead.CONFIDENTIALITIES
        ]

        options['status'] = [
            {
                'key': s[0],
                'value': s[1],
            } for s in Lead.STATUSES
        ]

        options['project'] = [
            {
                'key': project.id,
                'value': project.title,
            } for project in projects.distinct()
        ] if (fields is None or 'projects' in fields) else []

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
            ~models.Q(emm_risk_factor=''),
            ~models.Q(emm_risk_factor=None),
            lead__project__in=projects,
        ).values('emm_risk_factor').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_risk_factor'),
            label=models.F('emm_risk_factor'),
        ).order_by('emm_risk_factor')

        # Add info about if the project has emm leads, just check if entities or keywords present
        options['has_emm_leads'] = (not not options['emm_entities']) or (not not options['emm_keywords'])

        return response.Response(LegacyLeadOptionsSerializer(options).data)

    @swagger_auto_schema(
        request_body=LeadOptionsBodySerializer(),
        responses={200: LeadOptionsSerializer()}
    )
    def post(self, request, version=None):
        serializer = LeadOptionsBodySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.data
        projects_id = fields['projects']
        lead_groups_id = fields['lead_groups']
        organizations_id = fields['organizations']
        members_id = fields['members']
        emm_entities = fields['emm_entities']
        emm_keywords = fields['emm_keywords']
        emm_risk_factors = fields['emm_risk_factors']

        projects = Project.get_for_member(request.user).filter(
            id__in=projects_id,
        )
        if not projects.exists():
            raise exceptions.NotFound('Provided projects not found')

        project_filter = models.Q(project__in=projects)

        members_qs = User.objects.filter(id__in=members_id) if len(members_id) else User.objects

        options = {
            'projects': projects,

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

            'lead_groups': LeadGroup.objects.filter(project_filter, id__in=lead_groups_id).distinct(),
            'members': _filter_users_by_projects_memberships(members_qs, projects).prefetch_related('profile').distinct(),
            'organizations': Organization.objects.filter(id__in=organizations_id).distinct(),

            # EMM specific options
            'emm_entities': EMMEntity.objects.filter(
                lead__project__in=projects,
                name__in=emm_entities,
            ).distinct().values('name').annotate(
                total_count=models.Count('lead'),
                label=models.F('name'),
                key=models.F('id'),
            ).values('key', 'label', 'total_count').order_by('name'),

            'emm_keywords': LeadEMMTrigger.objects.filter(
                emm_keyword__in=emm_keywords,
                lead__project__in=projects
            ).values('emm_keyword').annotate(
                total_count=models.Sum('count'),
                key=models.F('emm_keyword'),
                label=models.F('emm_keyword')
            ).values('key', 'label', 'total_count').order_by('emm_keyword'),

            'emm_risk_factors': LeadEMMTrigger.objects.filter(
                emm_risk_factor__in=emm_risk_factors,
                lead__project__in=projects,
            ).values('emm_risk_factor').annotate(
                total_count=models.Sum('count'),
                key=models.F('emm_risk_factor'),
                label=models.F('emm_risk_factor'),
            ).order_by('emm_risk_factor'),

            'has_emm_leads': (
                EMMEntity.objects.filter(lead__project__in=projects).exists() or
                LeadEMMTrigger.objects.filter(lead__project__in=projects).exists()
            )
        }
        return response.Response(LeadOptionsSerializer(options).data)


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

    def get_organization(self, title, search):
        org = search.get(title)
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
        organization_search = OrganizationSearch([source_raw, author_raw])

        # LEGACY
        organization_context = {
            'source': source_raw,
            'author': author_raw,
        }
        if version != 'v1':
            organization_context = {
                'source': self.get_organization(source_raw, organization_search),
                'author': self.get_organization(author_raw, organization_search),
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
        def _get_clone_ready(obj, lead):
            obj.pk = None
            obj.lead = lead
            return obj

        preview = lead.leadpreview if hasattr(lead, 'leadpreview') else None
        preview_images = lead.images.all()
        emm_triggers = lead.emm_triggers.all()
        emm_entities = lead.emm_entities.all()

        lead.pk = None
        try:
            LeadSerializer.add_update__validate({
                'project': project_id,
            }, lead, lead.attachment)
        except serializers.ValidationError:
            return  # SKIP COPY if validation fails
        lead.project_id = project_id
        lead.save()

        # Clone Lead Preview (One-to-one fields)
        if preview:
            preview.pk = None
            preview.lead = lead
            preview.save()

        # Clone Many to many Fields
        lead.assignee.add(user)  # Assign requesting user
        lead.emm_entities.set(emm_entities)

        # Clone Many to one Fields
        LeadPreviewImage.objects.bulk_create([
            _get_clone_ready(image, lead) for image in preview_images
        ])
        LeadEMMTrigger.objects.bulk_create([
            _get_clone_ready(emm_trigger, lead) for emm_trigger in emm_triggers
        ])

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
