from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.template.response import TemplateResponse
from rest_framework import (
    exceptions,
    filters,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from rest_framework.decorators import detail_route, list_route
import django_filters

from docs.utils import mark_as_list, mark_as_delete
import ary.serializers as arys

from deep.permissions import ModifyPermission
from project.permissions import JoinPermission, AcceptRejectPermission
from project.models import ProjectRole
from project.filter_set import ProjectFilterSet, get_filtered_projects

from user.utils import send_project_join_request_emails
from user.models import User
from geo.models import Region
from user_group.models import UserGroup
from .models import (
    ProjectStatus,
    Project,
    ProjectMembership,
    ProjectJoinRequest
)
from .serializers import (
    ProjectSerializer,
    ProjectMembershipSerializer,
    ProjectJoinRequestSerializer,
)

from .token import project_request_token_generator
from deep.views import get_frontend_url

import logging

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = ProjectFilterSet
    search_fields = ('title', 'description',)

    def get_queryset(self):
        return get_filtered_projects(self.request.user, self.request.GET)

    """
    Get list of projects that user is member of
    """
    @list_route(permission_classes=[permissions.IsAuthenticated],
                serializer_class=ProjectSerializer,
                url_path='member-of')
    def get_for_member(self, request, version=None):
        user = self.request.GET.get('user', request.user)
        projects = Project.get_for_member(user)

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
    @detail_route(permission_classes=[permissions.IsAuthenticated],
                  url_path='analysis-framework')
    def get_framework(self, request, pk=None, version=None):
        from analysis_framework.serializers import AnalysisFrameworkSerializer
        from analysis_framework.models import AnalysisFramework

        project = self.get_object()
        if not project.analysis_framework:
            raise exceptions.NotFound('Resource not found')

        serializer = AnalysisFrameworkSerializer(
            project.analysis_framework,
            context={'request': request},
        )

        return response.Response(serializer.data)

    """
    Get assessment template for this project
    """
    @detail_route(permission_classes=[permissions.IsAuthenticated],
                  serializer_class=arys.AssessmentTemplateSerializer,
                  url_path='assessment-template')
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
    Join request to this project
    """
    @detail_route(permission_classes=[permissions.IsAuthenticated,
                                      JoinPermission],
                  methods=['post'],
                  url_path='join')
    def join_project(self, request, pk=None, version=None):
        project = self.get_object()
        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=request.user,
            status='pending',
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
    @detail_route(permission_classes=[permissions.IsAuthenticated,
                                      AcceptRejectPermission],
                  methods=['post'],
                  url_path=r'requests/(?P<request_id>\d+)/accept')
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
        if not role:
            role = ProjectRole.get_normal_role()
        else:
            role_qs = ProjectRole.objects.filter(id=role)
            if not role_qs.exists():
                return response.Response(
                    {'errors': 'Role id \'{}\' does not exist'.format(role)},
                    status=status.HTTP_404_NOT_FOUND
                )
            role = role_qs.first()
        ProjectViewSet._accept_request(request.user, join_request, role)

        serializer = ProjectJoinRequestSerializer(
            join_request,
            context={'request': request},
        )
        return response.Response(serializer.data)

    """
    Reject a join request to this project
    """
    @detail_route(permission_classes=[permissions.IsAuthenticated,
                                      AcceptRejectPermission],
                  methods=['post'],
                  url_path=r'requests/(?P<request_id>\d+)/reject')
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
    @detail_route(permission_classes=[permissions.IsAuthenticated],
                  methods=['post'],
                  url_path=r'join/cancel')
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
    @detail_route(permission_classes=[permissions.IsAuthenticated,
                                      ModifyPermission],
                  serializer_class=ProjectJoinRequestSerializer,
                  url_path='requests')
    def get_requests(self, request, pk=None, version=None):
        project = self.get_object()
        join_requests = project.projectjoinrequest_set.all()
        self.page = self.paginate_queryset(join_requests)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)


class ProjectMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        list = data and data.get('list')
        if list:
            kwargs.pop('data')
            kwargs.pop('many', None)
            return super(ProjectMembershipViewSet, self).get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super(ProjectMembershipViewSet, self).get_serializer(
            *args,
            **kwargs,
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.method == 'POST' and isinstance(response.data, list):
            response.data = {
                'results': response.data,
            }
        return super(ProjectMembershipViewSet, self).finalize_response(
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

            options['user_groups'] = [
                {
                    'key': user_group.id,
                    'value': user_group.title,
                } for user_group in user_groups.distinct()
            ]

        if (fields is None or 'status' in fields):
            options['status'] = [
                {
                    'key': status.id,
                    'value': status.title,
                } for status in ProjectStatus.objects.all()
            ]

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
        'notification_url': get_frontend_url('notifications/'),
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
