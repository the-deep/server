from rest_framework import (
    exceptions,
    permissions,
    response,
    views,
    viewsets,
)
from rest_framework.decorators import detail_route, list_route

from deep.permissions import ModifyPermission
from geo.models import Region
from user_group.models import UserGroup
from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer

import logging

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Project.get_for(self.request.user)

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
                {'key': 'active', 'value': 'Active'},
                {'key': 'inactive', 'value': 'Inactive'},
            ]

        return response.Response(options)
