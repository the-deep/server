from rest_framework import generics, viewsets, permissions
from deep.permissions import ModifyPermission

from .models import (
    GroupMembership,
    UserGroup,
)
from .serializers import (
    GroupMembershipSerializer,
    UserGroupSerializer,
)


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

    def get_serializer(self, instance=None,
                       data=None, many=False, partial=False):
        list = data.get('list')
        if list:
            return super(GroupMembershipViewSet, self).get_serializer(
                data=list,
                instance=instance,
                many=True,
                partial=partial,
            )

    def get_queryset(self):
        return GroupMembership.get_for(self.request.user)
