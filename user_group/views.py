from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import UserGroup, GroupMembership
from .serializers import UserGroupSerializer, GroupMembershipSerializer


class UserGroupViewSet(viewsets.ModelViewSet):
    serializer_class = UserGroupSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        return UserGroup.get_for(user)


class GroupMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return GroupMembership.get_for(self.request.user)
