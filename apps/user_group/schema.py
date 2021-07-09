from typing import Union

import graphene
from django.db.models import QuerySet, Exists, OuterRef
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import UserGroup, GroupMembership
from .filters import UserGroupFilterSet


class UserGroupType(DjangoObjectType):
    class Meta:
        model = UserGroup
        fields = '__all__'

    is_current_user_member = graphene.Boolean()

    def resolve_members(root, info, **kwargs) -> Union[QuerySet[GroupMembership], None]:
        if root.is_current_user_member:
            return root.members
        return GroupMembership.objects.none()

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.annotate(
            # Current user is member?
            is_current_user_member=Exists(
                GroupMembership.objects.filter(
                    group=OuterRef('pk'),
                    member=info.context.user,
                )
            )
        )


class UserGroupListType(CustomDjangoListObjectType):
    class Meta:
        model = UserGroup
        filterset_class = UserGroupFilterSet


class Query:
    user_group = DjangoObjectField(UserGroupType)
    user_groups = DjangoPaginatedListObjectField(
        UserGroupListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @classmethod
    def resolve_user_groups(cls, root, info, **kwargs):
        return UserGroupType.get_queryset(UserGroup.objects.all(), info)
