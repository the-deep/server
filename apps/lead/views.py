import copy
import re
import requests
import uuid as python_uuid

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.db import models, transaction

from deep import compiler  # noqa: F401
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

from deep.permissions import ModifyPermission, CreateLeadPermission, DeleteLeadPermission
from deep.paginations import AutocompleteSetPagination
from deep.authentication import CSRFExemptSessionAuthentication

from lead.filter_set import (
    LeadGroupFilterSet,
    LeadFilterSet,
)
from project.models import Project, ProjectMembership
from project.permissions import PROJECT_PERMISSIONS as PROJ_PERMS
from organization.models import Organization, OrganizationType
from organization.serializers import SimpleOrganizationSerializer
from utils.web_info_extractor import get_web_info_extractor
from utils.common import DEFAULT_HEADERS
from unified_connector.sources.base import OrganizationSearch
from entry.models import Entry

from .tasks import extract_from_lead
from .models import (
    LeadGroup,
    Lead,
    EMMEntity,
    LeadEMMTrigger,
    LeadPreviewImage,
)
from .serializers import (
    raise_or_return_existing_lead,
    LeadGroupSerializer,
    SimpleLeadGroupSerializer,
    LeadSerializer,
    LeadPreviewSerializer,
    check_if_url_exists,
    LeadOptionsSerializer,
    LeadOptionsBodySerializer,
    LegacyLeadOptionsSerializer,
    ExtractCallbackSerializer,
    DeduplicationCallbackSerializer,
)


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
    authentication_classes = [CSRFExemptSessionAuthentication]
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
    permission_classes = [permissions.IsAuthenticated, CreateLeadPermission,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    # NOTE: Using LeadFilterSet for both search and ordering
    filterset_class = LeadFilterSet

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
        filters = dict()
        filters['entries_filter_data'] = {
            f[0]: f[1] for f in self.request.data.pop('entries_filter', [])
        }
        if self.request.data.get('project'):
            project_id = self.request.data['project']
            if isinstance(project_id, list) and len(project_id) > 0:
                filters['entries_filter_data']['project'] = project_id[0]
            else:
                filters['entries_filter_data']['project'] = project_id
        leads = Lead.get_for(self.request.user, filters)

        lead_id = self.request.GET.get('similar')
        if lead_id:
            similar_lead = Lead.objects.get(id=lead_id)
            leads = leads.filter(project=similar_lead.project).annotate(
                similarity=TrigramSimilarity('title', similar_lead.title)
            ).filter(similarity__gt=0.3).order_by('-similarity')
        return leads

    # TODO: Remove this API endpoint after client is using summary
    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get', 'post'],
        url_path='emm-summary'
    )
    def emm_summary(self, request, version=None):
        return self.summary(request, version=version, emm_info_only=False)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get', 'post'],
        url_path='summary'
    )
    def summary(self, request, version=None, emm_info_only=False):
        if request.method == 'GET':
            qs = self.filter_queryset(self.get_queryset())
        elif request.method == 'POST':
            raw_filter_data = request.data
            filter_data = LeadFilterSet.get_processed_filter_data(raw_filter_data)
            qs = LeadFilterSet(data=filter_data, queryset=self.get_queryset()).qs
        emm_info = Lead.get_emm_summary(qs)
        if emm_info_only:
            return response.Response(emm_info)
        return response.Response({
            'total': qs.count(),
            'total_entries': Entry.objects.filter(lead__in=qs).count(),
            'total_controlled_entries': Entry.objects.filter(lead__in=qs, controlled=True).count(),
            'total_uncontrolled_entries': Entry.objects.filter(lead__in=qs, controlled=False).count(),
            **emm_info,
        })

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'leads_filter':
            context['post_is_used_for_filter'] = True
        return context

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post'],
        serializer_class=LeadSerializer,
        url_path='filter',
    )
    def leads_filter(self, request, version=None):
        raw_filter_data = request.data
        filter_data = LeadFilterSet.get_processed_filter_data(raw_filter_data)

        queryset = self.get_queryset()
        qs = LeadFilterSet(data=filter_data, queryset=queryset).qs
        page = self.paginate_queryset(qs)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(qs, many=True)
        response = self.get_paginated_response(serializer.data)

        return response


class LeadBulkDeleteViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, DeleteLeadPermission]

    def get_serializer_class(self):
        # required by ViewSchema generator
        return serializers.Serializer

    @action(
        detail=False,
        methods=['post'],
        url_path='dry-bulk-delete',
    )
    def dry_bulk_delete(self, request, project_id, version=None):
        lead_ids = request.data.get('leads', [])
        tbd_entities = Lead.get_associated_entities(project_id, lead_ids)
        return response.Response(tbd_entities, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='bulk-delete',
    )
    def bulk_delete(self, request, project_id, version=None):
        lead_ids = request.data.get('leads', [])
        Lead.objects.filter(project_id=project_id, id__in=lead_ids).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


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
            } for c in Lead.Confidentiality.choices
        ]

        options['status'] = [
            {
                'key': s[0],
                'value': s[1],
            } for s in Lead.Status.choices
        ]

        options['priority'] = [
            {
                'key': s[0],
                'value': s[1],
            } for s in Lead.Priority.choices
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

        options['organization_types'] = [
            {
                'key': organization_type.id,
                'value': organization_type.title,
            } for organization_type in OrganizationType.objects.all()
        ]
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
        organization_type_ids = fields['organization_types']

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
                } for c in Lead.Confidentiality.choices
            ],
            'status': [
                {
                    'key': s[0],
                    'value': s[1],
                } for s in Lead.Status.choices
            ],
            'priority': [
                {
                    'key': s[0],
                    'value': s[1],
                } for s in Lead.Priority.choices
            ],

            # Dynamic Options

            'lead_groups': LeadGroup.objects.filter(project_filter, id__in=lead_groups_id).distinct(),
            'members': _filter_users_by_projects_memberships(members_qs, projects)\
                                    .prefetch_related('profile').distinct(),
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
            ),
            'organization_types': OrganizationType.objects.filter(id__in=organization_type_ids).distinct(),
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


class WebInfoViewMixin():
    permission_classes = [permissions.IsAuthenticated]
    # FIXME: This is also used by chrome-extension, use csrf properly
    authentication_classes = [CSRFExemptSessionAuthentication]

    def get_organization(self, title, search):
        org = search.get(title)
        if org:
            return SimpleOrganizationSerializer(org).data

    def _process_data(
        self,
        request,
        organization_source_type,
        url,
        source_raw,
        authors_raw,
        country,
    ):
        project = None
        if country:
            project = Project.get_for_member(request.user).filter(
                regions__title__icontains=country
            ).first()
        project = project or request.user.profile.last_active_project
        organization_search = OrganizationSearch(
            [source_raw, *authors_raw],
            organization_source_type,
            request.user,
        )
        organization_context = {
            'source': self.get_organization(source_raw, organization_search),
            'authors': [
                self.get_organization(author, organization_search)
                for author in authors_raw
            ],
            'source_raw': source_raw,
            'authors_raw': authors_raw,
        }
        context = {
            **organization_context,
            'project': project and project.id,
            'existing': check_if_url_exists(url, request.user, project),
        }
        return context


# XXX: This is not used by client. Serverless (aws labmda) is used instead.
class WebInfoExtractView(WebInfoViewMixin, views.APIView):
    """
    Extract information from a website for new lead
    """
    def post(self, request, version=None):
        url = request.data.get('url')

        extractor = get_web_info_extractor(url)
        date = extractor.get_date()
        country = extractor.get_country()
        source_raw = extractor.get_source()
        authors_raw = extractor.get_author()
        title = extractor.get_title()

        context = self._process_data(
            request,
            Organization.SourceType.WEB_INFO_EXTRACT_VIEW,
            url=url,
            source_raw=source_raw,
            authors_raw=authors_raw,
            country=country,
        )

        return response.Response({
            **context,
            'title': title,
            'date': date,
            'country': country,
            'url': url,
        })


class WebInfoDataView(WebInfoViewMixin, views.APIView):
    """
    API for Web info Extra data after country, source and author extraction from
    the web info extraction service
    """

    def post(self, request, version=None):
        source_raw = request.data.get('source_raw')
        authors_raw = request.data.get('authors_raw')
        url = request.data.get('url')
        country = request.data.get('country')

        context = self._process_data(
            request,
            Organization.SourceType.WEB_INFO_DATA_VIEW,
            url=url,
            source_raw=source_raw,
            authors_raw=authors_raw,
            country=country,
        )
        return response.Response(context)


class BaseCopyView(views.APIView):
    """
    Copy object to another project

    Needs this attribute:
        - CLONE_PERMISSION
        - CLONE_ROLE
        - CLONE_ENTITY_NAME
        - CLONE_ENTITY
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        try:
            self.CLONE_PERMISSION
            self.CLONE_ROLE
            self.CLONE_ENTITY_NAME
            self.CLONE_ENTITY
        except AttributeError as e:
            raise Exception(f'{self.__class__.__name__} attributes are not defined properly', str(e))

    def get_clone_context(self, request):
        return {}

    # Clone Lead
    @classmethod
    def clone_entity(cls, original_lead, project_id, user, context):
        raise Exception('This method should be defined')

    @classmethod
    def get_project_ids_with_create_access(cls, request):
        """
        Project ids with create access for given entity
        """
        project_ids = ProjectMembership.objects.filter(
            project_id__in=request.data.get('projects', []),
            member=request.user,
        ).annotate(
            add_permission=models.F(cls.CLONE_ROLE).bitand(cls.CLONE_PERMISSION.create),
        ).filter(add_permission=cls.CLONE_PERMISSION.create).values_list('project_id', flat=True)
        return project_ids

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        context = self.get_clone_context(request)
        project_ids = self.get_project_ids_with_create_access(request)

        entities = self.CLONE_ENTITY.get_for(request.user).filter(pk__in=request.data.get(f'{self.CLONE_ENTITY_NAME}s', []))

        processed_entity = []
        processed_entity_by_project = {}
        for entity in entities:
            entity_original_project = entity.project_id
            processed_entity.append(entity.pk)

            edit_or_create_permission = self.CLONE_PERMISSION.create | self.CLONE_PERMISSION.modify
            edit_or_create_membership = ProjectMembership.objects.filter(
                member=request.user,
                project=entity.project,
            ).annotate(
                clone_perm=models.F(self.CLONE_ROLE).bitand(edit_or_create_permission)
            ).filter(clone_perm__gt=0).first()

            if not edit_or_create_membership:
                raise exceptions.PermissionDenied(
                    'You do not have enough permissions to'
                    f'clone {self.CLONE_ENTITY_NAME} from the project {entity.project.title}'
                )

            for project_id in project_ids:
                if project_id == entity_original_project:
                    continue

                # NOTE: To clone entity to another project
                p_entity = self.clone_entity(entity, project_id, request.user, context)
                if p_entity:
                    processed_entity_by_project[project_id] = (
                        processed_entity_by_project.get(project_id) or []
                    ) + [p_entity.pk]

        return response.Response({
            'projects': project_ids,
            f'{self.CLONE_ENTITY_NAME}s': processed_entity,
            f'{self.CLONE_ENTITY_NAME}s_by_projects': processed_entity_by_project,
        }, status=201)


class LeadCopyView(BaseCopyView):
    """
    Copy lead to another project
    """
    CLONE_PERMISSION = PROJ_PERMS.lead
    CLONE_ROLE = 'role__lead_permissions'
    CLONE_ENTITY_NAME = 'lead'
    CLONE_ENTITY = Lead

    @classmethod
    def clone_or_get_lead(cls, lead, project_id, user, context, create_access_project_ids):
        """Clone or return existing cloned Lead"""
        existing_lead = raise_or_return_existing_lead(
            project_id, lead, lead.source_type, lead.url, lead.text, lead.attachment, return_lead=True,
        )
        if existing_lead:
            return existing_lead, False

        # Skip if project_id not in create_access_project_ids
        if project_id not in create_access_project_ids:
            return None, False
        # Already checked for existing lead above
        return cls.clone_entity(lead, project_id, user, context, skip_existing_check=True), True

    # Clone Lead
    @classmethod
    def clone_entity(cls, original_lead, project_id, user, context, skip_existing_check=False):
        lead = copy.deepcopy(original_lead)

        def _get_clone_ready(obj, lead):
            obj.pk = None
            obj.lead = lead
            return obj

        # LeadGroup?
        preview = original_lead.leadpreview if hasattr(lead, 'leadpreview') else None
        preview_images = original_lead.images.all()
        emm_triggers = original_lead.emm_triggers.all()
        emm_entities = original_lead.emm_entities.all()
        authors = original_lead.authors.all()

        lead.pk = None
        lead.uuid = python_uuid.uuid4()
        try:
            # By default it raises error
            if not skip_existing_check:
                raise_or_return_existing_lead(
                    project_id, lead, lead.source_type, lead.url, lead.text, lead.attachment,
                )
            # return existing lead
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
        lead.authors.set(authors)

        # Clone Many to one Fields
        LeadPreviewImage.objects.bulk_create([
            _get_clone_ready(image, lead) for image in preview_images
        ])
        LeadEMMTrigger.objects.bulk_create([
            _get_clone_ready(emm_trigger, lead) for emm_trigger in emm_triggers
        ])

        return lead


class LeadExtractCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ExtractCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)


class LeadDeduplicationCallbackView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, **kwargs):
        serializer = DeduplicationCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response("Request successfully completed", status=status.HTTP_200_OK)
