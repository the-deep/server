import logging

import django_filters
from django.conf import settings
from django.db import transaction, models
from django.shortcuts import get_object_or_404
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

from docs.utils import mark_as_list, mark_as_delete
import ary.serializers as arys

from deep.views import get_frontend_url
from deep.permissions import ModifyPermission
from deep.serializers import URLCachedFileField
from deep.models import ProcessStatus
from tabular.models import Field

from user.utils import send_project_join_request_emails
from user.serializers import SimpleUserSerializer
from user.models import User
from geo.models import Region
from user_group.models import UserGroup
from geo.serializers import RegionSerializer
from entry.views import ComprehensiveEntriesViewSet
from .models import (
    ProjectStatus,
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectUserGroupMembership,
    ProjectEntryStats,
)
from .serializers import (
    ProjectSerializer,
    ProjectStatSerializer,
    ProjectRoleSerializer,
    ProjectMembershipSerializer,
    ProjectJoinRequestSerializer,
    ProjectUserGroupSerializer,
    ProjectDashboardSerializer,
    ProjectStatusOptionsSerializer,
)
from .permissions import (
    JoinPermission,
    AcceptRejectPermission,
    MembershipModifyPermission,
)
from .filter_set import (
    ProjectFilterSet,
    get_filtered_projects,
    ProjectMembershipFilterSet,
    ProjectUserGroupMembershipFilterSet,
)
from .tasks import generate_entry_stats

from .token import project_request_token_generator
logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = ProjectFilterSet
    search_fields = ('title', 'description',)

    def get_queryset(self):
        return get_filtered_projects(self.request.user, self.request.GET)

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
        url_path='entries-viz',
    )
    def get_entries_viz_data(self, request, pk=None, version=None):
        """
        Get viz data for project entries:
        """
        project = self.get_object()

        if (
                project.analysis_framework is None or
                project.analysis_framework.properties is None or
                project.analysis_framework.properties.get('stats_config') is None
        ):
            return response.Response(
                {'error': f'No configuration provided for current Project: {project.title}, Contact Admin'},
                status=status.HTTP_404_NOT_FOUND,
            )

        entry_stats, created = ProjectEntryStats.objects.get_or_create(project=project)
        file_url = request.build_absolute_uri(
            URLCachedFileField().to_representation(entry_stats.file)
        ) if entry_stats.file else None
        if entry_stats.is_ready():
            return response.Response({
                'data': file_url,
                'status': entry_stats.status,
            })
        elif entry_stats.status == ProcessStatus.FAILURE:
            return response.Response({
                'message': 'Failed to generate Entry stats, Contact Admin',
                'data': file_url,
                'status': entry_stats.status,
            })
        # TODO: Refactor task trigger if all users have access to this API
        generate_entry_stats.delay(project.pk)
        if entry_stats.status != ProcessStatus.PENDING:
            entry_stats.status = ProcessStatus.PENDING
            entry_stats.save()
        return response.Response({
            'message': 'Processing the request, try again later',
            'data': file_url,
            'status': entry_stats.status,
        }, status=status.HTTP_202_ACCEPTED)

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

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=request.user,
            status='pending',
            role=ProjectRole.get_default_role()
        )

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
        serializer_class=ProjectJoinRequestSerializer,
        url_path='requests',
    )
    def get_requests(self, request, pk=None, version=None):
        project = self.get_object()
        join_requests = project.projectjoinrequest_set.all()
        self.page = self.paginate_queryset(join_requests)
        serializer = self.get_serializer(self.page, many=True)
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
        project = self.get_object()
        viewfn = ComprehensiveEntriesViewSet.as_view({'get': 'list'})
        request._request.GET = request._request.GET.copy()
        request._request.GET['project'] = project.pk
        return viewfn(request._request, *args, **kwargs)

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=SimpleUserSerializer,
        url_path='members'
    )
    def get_members(self, request, pk=None, version=None):
        project = self.get_object()
        members = User.objects.filter(
            models.Q(projectmembership__project=project) |
            models.Q(usergroup__projectusergroupmembership__project=project)
        )
        self.page = self.paginate_queryset(members)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)


# FIXME: user better API
class ProjectStatViewSet(ProjectViewSet):
    serializer_class = ProjectStatSerializer

    def get_queryset(self):
        return get_filtered_projects(
            self.request.user, self.request.GET,
            annotate=True,
        )

    """
    Get dashboard related data for this project
    """
    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=ProjectDashboardSerializer,
        url_path='dashboard',
    )
    def get_dashboard(self, request, pk=None, version=None):
        project = self.get_object()
        serializer = self.get_serializer(project)
        return response.Response(serializer.data)


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

        options = {}

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

        if (fields is None or 'status' in fields):
            options['status'] = ProjectStatusOptionsSerializer(
                ProjectStatus.objects.all().prefetch_related('conditions'),
                many=True
            ).data

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
