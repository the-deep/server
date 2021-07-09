from typing import Union, List

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.serializers import URLCachedFileField

from .models import User
from .filters import UserFilterSet


def only_me(func):
    def wrapper(root, info, *args, **kwargs):
        if root == info.context.user:
            return func(root, info, *args, **kwargs)
    return wrapper


class UserType(DjangoObjectType):
    class Meta:
        model = User
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

    @staticmethod
    @only_me
    def resolve_display_picture(root, info, **kwargs) -> Union[str, None]:
        return root.profile.display_picture_id

    @staticmethod
    @only_me
    def resolve_display_picture_url(root, info, **kwargs) -> Union[str, None]:
        # NOTE: only passing this for current user.
        # TODO: Need to merge profile to user before enabling this for all users to avoid N+1 issue.
        # 3 table join is required right now.
        return root.profile.display_picture_id and info.context.request.build_absolute_uri(
            URLCachedFileField.name_to_representation(
                root.profile.display_picture.file.url
            )
        )

    @staticmethod
    @only_me
    def resolve_last_active_project(root, info, **kwargs) -> Union[int, None]:
        return root.profile.last_active_project_id

    @staticmethod
    @only_me
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


class UserListType(CustomDjangoListObjectType):
    class Meta:
        model = User
        filterset_class = UserFilterSet


class Query:
    me = graphene.Field(UserType)
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
