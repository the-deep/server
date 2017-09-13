from rest_framework import viewsets
from rest_framework import permissions

from .models import UserGroup, GroupMembership
from .serializers import UserGroupSerializer, GroupMembershipSerializer


class UserGroupPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return GroupMembership.objects.filter(
            role='admin',
            member=request.user,
            group=obj
        ).exists()


class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          UserGroupPermission]


class GroupMembershipPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return GroupMembership.objects.filter(
            role='admin',
            member=request.user,
            group=obj.group
        ).exists()


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          GroupMembershipPermission]
