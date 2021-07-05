from typing import Union

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import User
from .filters import UserFilterSet


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'is_active'
        )

    display_name = graphene.String()

    @staticmethod
    def resolve_display_name(root, info, **kwargs):
        return root.profile.get_display_name()


class MeUserType(UserType):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'last_login',
        )


# XXX: Is this okay to do?
class UserListType(CustomDjangoListObjectType):
    base_type = UserType

    class Meta:
        model = User
        filterset_class = UserFilterSet


class Query:
    me = graphene.Field(MeUserType)
    user = DjangoObjectField(UserType)
    users = DjangoPaginatedListObjectField(
        UserListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_me(root, info, **kwargs) -> Union[User, None]:
        if info.context.user.is_authenticated:
            return info.context.user
        return None
