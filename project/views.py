from rest_framework import viewsets
from rest_framework import permissions

from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer


class ProjectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return ProjectMembership.objects.filter(
            role='admin',
            member=request.user,
            project=obj
        ).exists()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          ProjectPermission]


class ProjectMembershipPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return ProjectMembership.objects.filter(
            role='admin',
            member=request.user,
            project=obj.project
        ).exists()


class ProjectMembershipViewSet(viewsets.ModelViewSet):
    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          ProjectMembershipPermission]
