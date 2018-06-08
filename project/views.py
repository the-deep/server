from django.shortcuts import get_object_or_404
from django.utils import timezone
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

from deep.permissions import ModifyPermission
from project.permissions import JoinPermission, AcceptRejectPermission
from project.filter_set import ProjectFilterSet, get_filtered_projects

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
                  url_path='assessment-template')
    def get_assessment_template(self, request, pk=None, version=None):
        from ary.serializers import AssessmentTemplateSerializer

        project = self.get_object()
        if not project.assessment_template:
            raise exceptions.NotFound('Resource not found')

        serializer = AssessmentTemplateSerializer(
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
        return response.Response(serializer.data,
                                 status=status.HTTP_201_CREATED)

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

        join_request.status = 'accepted'
        join_request.responded_by = request.user
        join_request.responded_at = timezone.now()
        join_request.save()

        ProjectMembership.objects.update_or_create(
            project=project,
            member=join_request.requested_by,
            defaults={
                'added_by': request.user,
            },
        )

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

        join_request.status = 'rejected'
        join_request.responded_by = request.user
        join_request.responded_at = timezone.now()
        join_request.save()

        serializer = ProjectJoinRequestSerializer(
            join_request,
            context={'request': request},
        )
        return response.Response(serializer.data)

    """
    Cancel a join request to this project
    """
    @detail_route(permission_classes=[permissions.IsAuthenticated],
                  methods=['post'],
                  url_path=r'join/cancel')
    def cancel_request(self, request, pk=None, version=None, request_id=None):
        project = self.get_object()
        join_request = get_object_or_404(ProjectJoinRequest,
                                         requested_by=request.user,
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
