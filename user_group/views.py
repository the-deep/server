from rest_framework import viewsets, permissions, status, response
from rest_framework.decorators import list_route
from django.db.models import Q, F, Value, CharField
from django.contrib.auth.models import User
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
        return UserGroup.get_for(self.request.user)

    @list_route(permission_classes=[permissions.IsAuthenticated],
                serializer_class=UserGroupSerializer,
                url_path='member-of')
    def get_for_member(self, request, version=None):
        user = self.request.GET.get('user', self.request.user)
        user_groups = UserGroup.get_for_member(user)

        self.page = self.paginate_queryset(user_groups)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)


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
            return super(GroupMembershipViewSet, self).get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super(GroupMembershipViewSet, self).get_serializer(
            *args,
            **kwargs,
        )

    def finalize_response(self, request, response, *args, **kwargs):
        if request.method == 'POST' and isinstance(response.data, list):
            response.data = {
                'results': response.data,
            }
        return super(GroupMembershipViewSet, self).finalize_response(
            request, response,
            *args, **kwargs,
        )

    def get_queryset(self):
        return GroupMembership.get_for(self.request.user)


class UserGroupUserSearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, version=None):
        query = request.query_params.get('query', '').strip().lower()
        if not query:
            return response.Response(
                {'errors': ['Empty query']},
                status=status.HTTP_400_BAD_REQUEST
            )
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).\
            annotate(title=F('username'), type=Value('user', CharField())).\
            values('id', 'title', 'type')
        user_groups = UserGroup.objects.filter(title__icontains=query).\
            annotate(type=Value('user_group', CharField())).\
            values('id', 'title', 'type')
        items = list(users) + list(user_groups)
        return response.Response(
            {'items': items}
        )
