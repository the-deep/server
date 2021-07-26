from django.db import models

from rest_framework import (
    permissions,
    viewsets,
)
from rest_framework.decorators import action

from deep.permissions import (
    ModifyPermission,
    IsUserGroupMember
)
from utils.db.functions import StrPos
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
        return UserGroup.get_for(self.request.user)

    @action(
        detail=False, permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserGroupSerializer,
        url_path='member-of',
    )
    def get_for_member(self, request, version=None):
        user = self.request.GET.get('user', self.request.user)
        user_groups = UserGroup.get_for_member(user)

        self.page = self.paginate_queryset(user_groups)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated, IsUserGroupMember],
        serializer_class=GroupMembershipSerializer,
        url_path='memberships',
    )
    def get_usergroup_member(self, request, pk, version=None):
        user_group = self.get_object()
        members = GroupMembership.get_member_for_user_group(user_group)
        self.page = self.paginate_queryset(members)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # Check if project exclusion query is present
        exclude_project = self.request.query_params.get(
            'members_exclude_project')
        if exclude_project:
            queryset = queryset.filter(
                ~models.Q(projectusergroupmembership__project=exclude_project)
            ).distinct()

        search_str = self.request.query_params.get('search')
        if search_str is None or not search_str.strip():
            return queryset

        return queryset.annotate(
            strpos=StrPos(
                models.functions.Lower('title'),
                models.Value(search_str.lower(), models.CharField())
            )
        ).filter(strpos__gte=1).order_by('strpos')


class GroupMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

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
        return GroupMembership.get_for(self.request.user)
