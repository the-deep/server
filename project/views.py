from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer


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

    def get_serializer(self, instance=None,
                       data=None, many=False, partial=False):
        list = data.get('list')
        if list:
            return super(ProjectMembershipViewSet, self).get_serializer(
                data=list,
                instance=instance,
                many=True,
                partial=partial,
            )

    def get_queryset(self):
        return ProjectMembership.get_for(self.request.user)
