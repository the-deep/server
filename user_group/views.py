import logging

from rest_framework import (
    exceptions,
    mixins,
    permissions,
    viewsets,
)
from rest_framework.decorators import list_route
from django.db import models

from django.contrib.auth.models import User
from deep.permissions import ModifyPermission

from .models import (
    GroupMembership,
    UserGroup,
)
from .serializers import (
    GroupMembershipSerializer,
    UserGroupSerializer,
    UserGroupUserSerializer,
)

logger = logging.getLogger(__name__)


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


class UserGroupUserSearchViewSet(viewsets.GenericViewSet,
                                 mixins.ListModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserGroupUserSerializer

    def get_queryset(self):
        query = self.request.query_params.get('search', '').strip().lower()
        if not query:
            raise exceptions.ValidationError('Empty search string')

        # We have to rename each field of users and usergroups query
        # so that the selected fields will have same name and
        # can be merged together using union to a single query set.

        users = User.objects.filter(
            models.Q(username__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query)
        ).values(
            entity_id=models.F('id'),
            entity_username=models.F('username'),
            entity_first_name=models.F('first_name'),
            entity_last_name=models.F('last_name'),
            entity_display_picture=models.F('profile__display_picture'),

            entity_title=models.Value(None, models.CharField()),
            entity_type=models.Value('user', models.CharField()),
        )

        user_groups = UserGroup.objects.filter(
            title__icontains=query
        ).values(
            entity_id=models.F('id'),
            entity_title=models.F('title'),

            entity_username=models.Value(None, models.CharField()),
            entity_first_name=models.Value(None, models.CharField()),
            entity_last_name=models.Value(None, models.CharField()),
            entity_type=models.Value('user_group', models.CharField()),
            entity_display_picture=models.Value(None, models.IntegerField()),
        )

        project = self.request.query_params.get('project')
        if project:
            users = users.exclude(project__id=project)
            user_groups = user_groups.exclude(project__id=project)

        entities = users.union(user_groups)
        logger.debug(entities.query)

        def sort_key(item):
            # The less the query's index, better the relevance
            if item['entity_type'] == 'user':
                return max([
                    item['entity_username'].find(query),
                    item['entity_username'].find(query),
                    item['entity_username'].find(query),
                ])
            elif item['entity_type'] == 'user_group':
                return item['entity_title'].find(query) \
                    if item['entity_title'] else -1
            else:
                return -1

        sorted_entities = sorted(entities, key=sort_key)
        return sorted_entities
