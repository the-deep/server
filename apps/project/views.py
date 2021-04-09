import logging
import uuid

from dateutil.relativedelta import relativedelta
import django_filters
from django.db import connection as django_db_connection
from django.conf import settings
from django.http import Http404
from django.db import transaction, models
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework import (
    exceptions,
    filters,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from docs.utils import mark_as_list, mark_as_delete
import ary.serializers as arys

from deep.views import get_frontend_url
from deep.permissions import (
    ModifyPermission,
    IsProjectMember,
)
from deep.serializers import URLCachedFileField
from deep.models import ProcessStatus
from deep.paginations import SmallSizeSetPagination
from tabular.models import Field

from user.utils import send_project_join_request_emails
from user.serializers import SimpleUserSerializer
from user.models import User
from lead.models import Lead
from lead.views import ProjectLeadGroupViewSet
from geo.models import Region
from user_group.models import UserGroup
from geo.serializers import RegionSerializer
from entry.models import Entry
from entry.views import ComprehensiveEntriesViewSet
from analysis.models import (
    Analysis,
    AnalyticalStatement,
    AnalyticalStatementEntry
)

from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectUserGroupMembership,
    ProjectStats,
    ProjectOrganization
)
from .serializers import (
    ProjectSerializer,
    ProjectStatSerializer,
    ProjectRoleSerializer,
    ProjectMembershipSerializer,
    ProjectJoinRequestSerializer,
    ProjectUserGroupSerializer,
    ProjectMemberViewSerializer,
    ProjectRecentActivitySerializer,
)
from .permissions import (
    JoinPermission,
    AcceptRejectPermission,
    MembershipModifyPermission,
    PROJECT_PERMISSIONS,
)
from .filter_set import (
    ProjectFilterSet,
    get_filtered_projects,
    ProjectMembershipFilterSet,
    ProjectUserGroupMembershipFilterSet,
)
from .tasks import generate_viz_stats

from .token import project_request_token_generator
logger = logging.getLogger(__name__)


def _get_viz_data(request, project, can_view_confidential, token=None):
    """
    Util function to trigger and serve Project entry/ary viz data
    """
    if (
            project.analysis_framework is None or
            project.analysis_framework.properties is None or
            project.analysis_framework.properties.get('stats_config') is None
    ):
        return {
            'error': f'No configuration provided for current Project: {project.title}, Contact Admin',
        }, status.HTTP_404_NOT_FOUND

    stats, created = ProjectStats.objects.get_or_create(project=project)

    if token and token != str(stats.token):
        return {'error': 'Token is invalid'}, status.HTTP_403_FORBIDDEN

    stat_file = stats.confidential_file if can_view_confidential else stats.file
    file_url = (
        request.build_absolute_uri(URLCachedFileField().to_representation(stat_file))
        if stat_file else None
    )
    stats_meta = {
        'data': file_url,
        'modified_at': stats.modified_at,
        'status': stats.status,
        'public_url': stats.get_public_url(request),
    }

    if stats.is_ready():
        return stats_meta, status.HTTP_200_OK
    elif stats.status == ProcessStatus.FAILURE:
        return {
            'error': 'Failed to generate stats, Contact Admin',
            **stats_meta,
        }, status.HTTP_200_OK
    transaction.on_commit(lambda: generate_viz_stats.delay(project.pk))
    # NOTE: Not changing modified_at if already pending
    if stats.status != ProcessStatus.PENDING:
        stats.status = ProcessStatus.PENDING
        stats.save()
    return {
        'message': 'Processing the request, try again later',
        **stats_meta,
    }, status.HTTP_202_ACCEPTED


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = ProjectFilterSet
    search_fields = ('title', 'description',)

    def get_queryset(self):
        return get_filtered_projects(self.request.user, self.request.GET)

    def get_serializer_class(self):
        # get the project and check for its member with current user
        if (self.lookup_url_kwarg or self.lookup_field) not in self.kwargs:
            return ProjectSerializer
        project = self.get_object()
        if project.members.filter(id=self.request.user.id).exists():
            return ProjectMemberViewSerializer
        return ProjectSerializer

    def get_project_object(self):
        """
        Return project same as get_object without any other filters
        """
        if self.kwargs.get('pk') is not None:
            return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        raise Http404

    @action(
        detail=False,
        url_path='recent-activities',
    )
    def get_recent_activities(self, request, version=None):
        return response.Response({
            'results': ProjectRecentActivitySerializer(
                Project.get_recent_activities(request.user),
                context={'request': request}, many=True,
            ).data
        })

    """
    Get list of projects that user is member of
    """
    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='member-of',
    )
    def get_for_member(self, request, version=None):
        user = self.request.GET.get('user')
        projects = Project.get_for_member(user)

        if user is None or request.user == user:
            projects = Project.get_for_member(request.user)
        else:
            projects = Project.get_for_public(request.user, user)

        user_group = request.GET.get('user_group')
        if user_group:
            user_group = user_group.split(',')
            projects = projects.filter(user_groups__id__in=user_group)

        self.page = self.paginate_queryset(projects)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)

    """
    Generate project public VIZ URL
    """
    @action(
        detail=True,
        methods=['post'],
        url_path='public-viz',
    )
    def generate_public_viz(self, request, pk=None, version=None):
        project = self.get_object()
        action = request.data.get('action', 'set')
        stats, created = ProjectStats.objects.get_or_create(project=project)
        if action == 'set':
            stats.token = uuid.uuid4()
        elif action == 'unset':
            stats.token = None
        else:
            raise exceptions.ValidationError({'action': f'Invalid action {action}'})
        stats.save(update_fields=['token'])
        return response.Response({'public_url': stats.get_public_url(request)})

    """
    Get analysis framework for this project
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path='analysis-framework'
    )
    def get_framework(self, request, pk=None, version=None):
        from analysis_framework.serializers import AnalysisFrameworkSerializer

        project = self.get_object()
        if not project.analysis_framework:
            raise exceptions.NotFound('Resource not found')

        serializer = AnalysisFrameworkSerializer(
            project.analysis_framework,
            context={'request': request},
        )

        return response.Response(serializer.data)

    """
    Get regions assigned to this project
    """
    @action(
        detail=True,
        url_path='regions',
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_regions(self, request, pk=None, version=None):
        instance = self.get_object()
        serializer = RegionSerializer(
            instance.regions,
            many=True, context={'request': request},
        )
        return response.Response({'regions': serializer.data})

    """
    Get assessment template for this project
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=arys.AssessmentTemplateSerializer,
        url_path='assessment-template',
    )
    def get_assessment_template(self, request, pk=None, version=None):
        project = self.get_object()
        if not project.assessment_template:
            raise exceptions.NotFound('Resource not found')

        serializer = arys.AssessmentTemplateSerializer(
            project.assessment_template,
            context={'request': request},
        )

        return response.Response(serializer.data)

    """
    Get status for export:
    -   tabular chart generation status
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=ProjectJoinRequestSerializer,
        url_path='export-status',
    )
    def get_export_status(self, request, pk=None, version=None):
        project = self.get_object()
        fields_pending_count = Field.objects.filter(
            cache__image_status=Field.CACHE_PENDING,
            sheet__book__project=project,
        ).count()
        return response.Response({
            'tabular_pending_fields_count': fields_pending_count,
        })

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path='project-viz',
    )
    def get_project_viz_data(self, request, pk=None, version=None):
        """
        Get viz data for project entries:
        """
        project = self.get_object()
        can_view_confidential = (
            ProjectMembership.objects
            .filter(member=request.user, project=project)
            .annotate(
                view_all=models.F('role__lead_permissions').bitand(PROJECT_PERMISSIONS.lead.view)
            )
            .filter(view_all=PROJECT_PERMISSIONS.lead.view)
            .exists()
        )
        context, status_code = _get_viz_data(request, project, can_view_confidential)
        return response.Response(context, status=status_code)

    """
    Join request to this project
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated, JoinPermission],
        methods=['post'],
        url_path='join',
    )
    def join_project(self, request, pk=None, version=None):
        project = self.get_object()

        # Forbid join requests for private project
        if (project.is_private):
            raise PermissionDenied(
                {'message': "You cannot send join request to the private project"}
            )

        serializer = ProjectJoinRequestSerializer(
            data={
                'role': ProjectRole.get_default_role().id,
                **request.data,
            },
            context={'request': request, 'project': project}
        )
        serializer.is_valid(raise_exception=True)
        join_request = serializer.save()

        serializer = ProjectJoinRequestSerializer(
            join_request,
            context={'request': request},
        )

        if settings.TESTING:
            send_project_join_request_emails(join_request.id)
        else:
            # Unless we are in test environment,
            # send the join request emails in a celery
            # background task.
            # This makes sure that the response is returned
            # while the emails are being sent in the background.
            def send_mail():
                send_project_join_request_emails.delay(join_request.id)
            transaction.on_commit(send_mail)

        return response.Response(serializer.data,
                                 status=status.HTTP_201_CREATED)

    @staticmethod
    def _accept_request(responded_by, join_request, role):
        if not role or role == 'normal':
            role = ProjectRole.get_default_role()
        elif role == 'admin':
            role = ProjectRole.get_default_admin_role()
        else:
            role_qs = ProjectRole.objects.filter(id=role)
            if not role_qs.exists():
                return response.Response(
                    {'errors': 'Role id \'{}\' does not exist'.format(role)},
                    status=status.HTTP_404_NOT_FOUND
                )
            role = role_qs.first()

        join_request.status = 'accepted'
        join_request.responded_by = responded_by
        join_request.responded_at = timezone.now()
        join_request.role = role
        join_request.save()

        ProjectMembership.objects.update_or_create(
            project=join_request.project,
            member=join_request.requested_by,
            defaults={
                'role': role,
                'added_by': responded_by,
            },
        )

    @staticmethod
    def _reject_request(responded_by, join_request):
        join_request.status = 'rejected'
        join_request.responded_by = responded_by
        join_request.responded_at = timezone.now()
        join_request.save()

    """
    Accept a join request to this project,
    creating the membership while doing so.
    """
    @action(
        detail=True,
        permission_classes=[
            permissions.IsAuthenticated, AcceptRejectPermission,
        ],
        methods=['post'],
        url_path=r'requests/(?P<request_id>\d+)/accept',
    )
    def accept_request(self, request, pk=None, version=None, request_id=None):
        project = self.get_object()
        join_request = get_object_or_404(ProjectJoinRequest,
                                         id=request_id,
                                         project=project)

        if join_request.status in ['accepted', 'rejected']:
            raise exceptions.ValidationError(
                'This request has already been {}'.format(join_request.status)
            )

        role = request.data.get('role')
        ProjectViewSet._accept_request(request.user, join_request, role)

        serializer = ProjectJoinRequestSerializer(
            join_request,
            context={'request': request},
        )
        return response.Response(serializer.data)

    """
    Reject a join request to this project
    """
    @action(
        detail=True,
        permission_classes=[
            permissions.IsAuthenticated, AcceptRejectPermission,
        ],
        methods=['post'],
        url_path=r'requests/(?P<request_id>\d+)/reject',
    )
    def reject_request(self, request, pk=None, version=None, request_id=None):
        project = self.get_object()
        join_request = get_object_or_404(ProjectJoinRequest,
                                         id=request_id,
                                         project=project)

        if join_request.status in ['accepted', 'rejected']:
            raise exceptions.ValidationError(
                'This request has already been {}'.format(join_request.status)
            )

        ProjectViewSet._reject_request(request.user, join_request)

        serializer = ProjectJoinRequestSerializer(
            join_request,
            context={'request': request},
        )
        return response.Response(serializer.data)

    """
    Cancel a join request to this project
    """
    @mark_as_delete()
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post'],
        url_path=r'join/cancel',
    )
    def cancel_request(self, request, pk=None, version=None, request_id=None):
        project = self.get_object()
        join_request = get_object_or_404(ProjectJoinRequest,
                                         requested_by=request.user,
                                         status='pending',
                                         project=project)

        if join_request.status in ['accepted', 'rejected']:
            raise exceptions.ValidationError(
                'This request has already been {}'.format(join_request.status)
            )

        join_request.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    """
    Get list of join requests for this project
    """
    @mark_as_list()
    @action(
        detail=True,
        permission_classes=[
            permissions.IsAuthenticated, ModifyPermission,
        ],
        url_path='requests',
    )
    def get_requests(self, request, pk=None, version=None):
        project = self.get_object()
        join_requests = project.projectjoinrequest_set.all()
        self.page = self.paginate_queryset(join_requests)
        serializer = ProjectJoinRequestSerializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)

    """
    Comprehensive Entries
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get'],
        url_path=r'comprehensive-entries',
    )
    def comprehensive_entries(self, request, *args, **kwargs):
        project = self.get_project_object()
        viewfn = ComprehensiveEntriesViewSet.as_view({'get': 'list'})
        request._request.GET = request._request.GET.copy()
        request._request.GET['project'] = project.pk
        return viewfn(request._request, *args, **kwargs)

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated, IsProjectMember],
        url_path='members'
    )
    def get_members(self, request, pk=None, version=None):
        project = self.get_object()
        members = User.objects.filter(
            models.Q(projectmembership__project=project) |
            models.Q(usergroup__projectusergroupmembership__project=project)
        ).distinct()
        self.page = self.paginate_queryset(members)
        serializer = SimpleUserSerializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)

    """
    Project Lead-Groups
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get'],
        url_path=r'lead-groups',
    )
    def get_lead_groups(self, request, *args, **kwargs):
        project = self.get_project_object()
        viewfn = ProjectLeadGroupViewSet.as_view({'get': 'list'})
        request._request.GET = request._request.GET.copy()
        request._request.GET['project'] = project.pk
        return viewfn(request._request)

    """
    Project Questionnaire Meta
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['get'],
        url_path=r'questionnaire-meta',
    )
    def get_questionnaire_meta(self, request, *args, **kwargs):
        project = self.get_project_object()
        af = project.analysis_framework
        meta = {
            'active_count': project.questionnaire_set.filter(is_archived=False).count(),
            'archived_count': project.questionnaire_set.filter(is_archived=True).count(),
            'analysis_framework': af and {
                'id': af.id,
                'title': af.title,
            },
        }
        return response.Response(meta)

    """
    Get analysis for this project
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated, IsProjectMember],
        url_path='analysis-overview'
    )
    def get_analysis(self, request, pk=None, version=None):
        project = self.get_object()
        # get all the analysis in the project
        analysis_list = Analysis.objects.filter(
            project=project
        ).values('id', 'title', 'created_at')

        leads = Lead.objects.filter(project=project)
        total_sources = leads.annotate(entries_count=models.Count('entry')).filter(entries_count__gt=0).count()
        entries_total = Entry.objects.filter(project=project).count()
        entries_analyzed = AnalyticalStatement.objects.filter(
            analysis_pillar__analysis__project=project
        ).values('entries').distinct().count()
        analyzed_source = AnalyticalStatement.objects.filter(
            analysis_pillar__analysis__project=project
        ).values('entries__lead_id').distinct().count()

        lead_qs = Lead.objects.filter(
            project=project,
            authors__isnull=False
        ).annotate(
            entries_count=models.functions.Coalesce(models.Subquery(
                AnalyticalStatementEntry.objects.filter(
                    entry__lead_id=models.OuterRef('pk')
                ).order_by().values('entry__lead_id').annotate(count=models.Count('*'))
                .values('count')[:1],
                output_field=models.IntegerField(),
            ), 0)
        ).filter(entries_count__gt=0)
        authoring_organizations = Lead.objects.filter(id__in=lead_qs).order_by('authors__organization_type').values(
            'authors__organization_type'
        ).annotate(count=models.Count('id')).values(
            'count',
            organization_type_id=models.F('authors__organization_type'),
            organization_type_title=models.F('authors__organization_type__title')
        )
        return response.Response({
            'analysis_list': analysis_list,
            'entries_total': entries_total,
            'analyzed_entries_count': entries_analyzed,
            'sources_total': total_sources,
            'analyzed_source_count': analyzed_source,
            'authoring_organizations': authoring_organizations
        })


class ProjectStatViewSet(ProjectViewSet):
    pagination_class = SmallSizeSetPagination

    def get_serializer_class(self):
        return ProjectStatSerializer

    def get_queryset(self):
        return get_filtered_projects(
            self.request.user, self.request.GET,
            annotate=True,
        ).prefetch_related(
            'regions', 'organizations',
        ).select_related(
            'created_by__profile', 'modified_by__profile'
        )

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='recent'
    )
    def get_recent_projects(self, request, *args, **kwargs):
        # NOTE: Django ORM union don't allow annotation
        with django_db_connection.cursor() as cursor:
            select_sql = [
                f'''
                    SELECT
                        tb."project_id" AS "project",
                        MAX(tb."{field}_at") AS "date"
                    FROM "{Model._meta.db_table}" AS tb
                    WHERE tb."{field}_by_id" = {request.user.pk}
                    GROUP BY tb."project_id"
                ''' for Model, field in [
                    (Lead, 'created'),
                    (Lead, 'modified'),
                    (Entry, 'created'),
                    (Entry, 'modified'),
                ]
            ]
            union_sql = '(' + ') UNION ('.join(select_sql) + ')'
            cursor.execute(
                f'SELECT DISTINCT(entities."project"), MAX("date") as "date" FROM ({union_sql}) as entities'
                f' GROUP BY entities."project" ORDER BY "date" DESC'
            )
            recent_projects_id = [pk for pk, _ in cursor.fetchall()]
        # Only pull project data for which user is member of
        qs = self.get_queryset().filter(Project.get_query_for_member(request.user))
        current_users_project_id = set(qs.filter(pk__in=recent_projects_id).values_list('pk', flat=True))
        recent_projects_id = [pk for pk in recent_projects_id if pk in current_users_project_id][:3]
        projects_map = {
            project.pk: project
            for project in qs.filter(pk__in=recent_projects_id)
        }
        # Maintain the order
        recent_projects = [
            projects_map[id]
            for id in recent_projects_id if projects_map.get(id)
        ]
        return response.Response(
            self.get_serializer_class()(
                recent_projects,
                context=self.get_serializer_context(),
                many=True,
            ).data
        )

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='summary'
    )
    def get_projects_summary(self, request, pk=None, version=None):
        projects = Project.get_for_member(request.user)
        # Lead stats
        leads = Lead.objects.filter(project__in=projects)
        total_leads_tagged_count = leads.annotate(entries_count=models.Count('entry')).filter(entries_count__gt=0).count()
        total_leads_tagged_and_verified_count = leads.annotate(
            entries_count=models.Count('entry'),
            verified_entries_count=models.Count(
                'entry', filter=models.Q(entry__verified=True)
            ),
        ).filter(entries_count__gt=0, entries_count=models.F('verified_entries_count')).count()
        # Entries activity
        recent_entries = Entry.objects.filter(
            project__in=projects,
            created_at__gte=(timezone.now() + relativedelta(months=-3))
        )
        recent_entries_activity = {
            'projects': (
                recent_entries.order_by().values('project')
                .annotate(count=models.Count('*'))
                .filter(count__gt=0)
                .values('count', id=models.F('project'), title=models.F('project__title'))
            ),
            'activities': (
                recent_entries.order_by('project', 'created_at__date').values('project', 'created_at__date')
                .annotate(count=models.Count('*'))
                .values('project', 'count', date=models.Func(models.F('created_at__date'), function='DATE'))
            ),
        }
        return response.Response({
            'projects_count': projects.count(),
            'total_leads_count': leads.count(),
            'total_leads_tagged_count': total_leads_tagged_count,
            'total_leads_tagged_and_verified_count': total_leads_tagged_and_verified_count,
            'recent_entries_activity': recent_entries_activity,
        })


class ProjectMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission, MembershipModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = ProjectMembershipFilterSet

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        list = data and data.get('list')
        if list:
            kwargs.pop('data')
            kwargs.pop('many', None)
            return super().get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super().get_serializer(
            *args,
            **kwargs,
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.method == 'POST' and isinstance(response.data, list):
            response.data = {
                'results': response.data,
            }
        return super().finalize_response(
            request, response,
            *args, **kwargs,
        )

    def get_queryset(self):
        return ProjectMembership.get_for(self.request.user)


class ProjectOptionsView(views.APIView):
    """
    Options for various attributes related to project
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        project_query = request.GET.get('project')
        fields_query = request.GET.get('fields')

        projects = None
        if project_query:
            projects = Project.get_for(request.user).filter(
                id__in=project_query.split(',')
            )

        fields = None
        if fields_query:
            fields = fields_query.split(',')

        options = {
            'project_organization_types': [
                {
                    'key': s[0],
                    'value': s[1],
                } for s in ProjectOrganization.ORGANIZATION_TYPES
            ],
        }

        def _filter_by_projects(qs, projects):
            for p in projects:
                qs = qs.filter(project=p)
            return qs

        if (fields is None or 'regions' in fields):
            if projects:
                regions1 = _filter_by_projects(Region.objects, projects)
            else:
                regions1 = Region.objects.none()
            regions2 = Region.get_for(request.user).distinct()
            regions = regions1.union(regions2)

            options['regions'] = [
                {
                    'key': region.id,
                    'value': region.get_verbose_title(),
                } for region in regions.distinct()
            ]

        if (fields is None or 'user_groups' in fields):
            if projects:
                user_groups1 = _filter_by_projects(UserGroup.objects, projects)
            else:
                user_groups1 = UserGroup.objects.none()
            user_groups2 = UserGroup.get_modifiable_for(request.user)\
                .distinct()
            user_groups = user_groups1.union(user_groups2)

            options['user_groups'] = user_groups.distinct().annotate(
                key=models.F('id'),
                value=models.F('title')
            ).values('key', 'value')

        if (fields is None or 'involvement' in fields):
            options['involvement'] = [
                {'key': 'my_projects', 'value': 'My projects'},
                {'key': 'not_my_projects', 'value': 'Not my projects'}
            ]

        return response.Response(options)


def accept_project_confirm(
    request, uidb64, pidb64, token,
    template_name='project/project_join_request_confirm.html',
):
    accept = request.GET.get('accept', 'True').lower() == 'true'
    role = request.GET.get('role', 'normal')
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        pid = force_text(urlsafe_base64_decode(pidb64))
        user = User.objects.get(pk=uid)
        join_request = ProjectJoinRequest.objects.get(pk=pid)
    except(
        TypeError, ValueError, OverflowError,
        ProjectJoinRequest.DoesNotExist, User.DoesNotExist,
    ):
        user = None
        join_request = None

    request_data = {
        'join_request': join_request,
        'will_responded_by': user,
    }
    context = {
        'title': 'Project Join Request',
        'success': True,
        'accept': accept,
        'role': role,
        'frontend_url': get_frontend_url(''),
        'join_request': join_request,
        'project_url': get_frontend_url(
            'projects/{}/#/general'.format(join_request.project.id)
        ) if join_request else None,
    }

    if (join_request and user) is not None and\
            project_request_token_generator.check_token(request_data, token):
        if accept:
            ProjectViewSet._accept_request(user, join_request, role)
        else:
            ProjectViewSet._reject_request(user, join_request)
    else:
        context['success'] = False

    return TemplateResponse(request, template_name, context)


class ProjectRoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProjectRole.objects.all()


class ProjectUserGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectUserGroupSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    queryset = ProjectUserGroupMembership.objects.all()
    filterset_class = ProjectUserGroupMembershipFilterSet
