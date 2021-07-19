import time

from typing import Union, List

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.utils import timezone

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from jwt_auth.token import AccessToken

from .models import User
from .filters import UserFilterSet


def only_me(func):
    def wrapper(root, info, *args, **kwargs):
        if root == info.context.user:
            return func(root, info, *args, **kwargs)
    return wrapper


class JwtTokenType(graphene.ObjectType):
    access_token = graphene.String()
    expires_in = graphene.String()


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'is_active',
        )

    display_name = graphene.String()
    # Profile fields
    display_picture_url = graphene.String()
    organization = graphene.String()
    language = graphene.String()

    @staticmethod
    def resolve_display_picture_url(root, info, **kwargs) -> Union[str, None]:
        # TODO: Need to merge profile to user before enabling this for all users to avoid N+1 issue.
        # 3 table join is required right now.
        return info.context.dl.user.display_picture.load(root.id)

    @staticmethod
    def resolve_organization(root, info, **kwargs) -> Union[str, None]:
        return info.context.dl.user.organization.load(root.id)


class UserMeType(DjangoObjectType):
    class Meta:
        model = User
        skip_registry = True
        fields = (
            'id', 'first_name', 'last_name', 'is_active',
            'email', 'last_login',
        )

    display_name = graphene.String()
    email = graphene.String()  # To make this field nullable in Model
    # Profile fields
    display_picture = graphene.ID()
    display_picture_url = graphene.String()
    organization = graphene.String()
    language = graphene.String()
    last_active_project = graphene.ID()
    email_opt_outs = graphene.List(graphene.String)
    jwt_token = graphene.Field(JwtTokenType)

    @staticmethod
    @only_me
    def resolve_display_picture(root, info, **kwargs) -> Union[str, None]:
        return root.profile.display_picture_id

    @staticmethod
    @only_me
    def resolve_last_active_project(root, info, **kwargs) -> Union[int, None]:
        return root.profile.last_active_project_id

    @staticmethod
    def resolve_organization(root, info, **kwargs) -> Union[str, None]:
        return root.profile.organization

    @staticmethod
    @only_me
    def resolve_language(root, info, **kwargs) -> Union[str, None]:
        return root.profile.language

    @staticmethod
    @only_me
    def resolve_email_opt_outs(root, info, **kwargs) -> Union[List[str], None]:
        return root.profile.email_opt_outs

    @staticmethod
    @only_me
    def resolve_email(root, info, **kwargs) -> Union[str, None]:
        return root.email

    @staticmethod
    @only_me
    def resolve_last_login(root, info, **kwargs) -> Union[str, None]:
        return root.last_login

    @staticmethod
    @only_me
    def resolve_jwt_token(root, info, **kwargs) -> Union[JwtTokenType, None]:
        access_token = AccessToken.for_user(info.context.user)  # Only for current user
        return JwtTokenType(
            access_token=access_token,
            expires_in=time.mktime((timezone.now() + AccessToken.lifetime).timetuple()),
        )


class UserListType(CustomDjangoListObjectType):
    class Meta:
        model = User
        filterset_class = UserFilterSet


class Query:
    me = graphene.Field(UserMeType)
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
