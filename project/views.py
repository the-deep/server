from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer

import logging

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        projects = Project.get_for(user)

        user_group = self.request.GET.get('user_group')
        if user_group:
            user_group = user_group.split(',')
            projects = projects.filter(user_groups=user_group)

        return projects


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
