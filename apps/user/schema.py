import time
import datetime

from typing import Union, List

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.utils import timezone
from django.conf import settings
from django.db import models

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from jwt_auth.token import AccessToken
from deep.serializers import URLCachedFileField

from project.models import (
    Project,
    ProjectMembership,
    ProjectRole,
)

from .models import User, Feature
from .enums import UserEmailConditionOptOutEnum
from .filters import UserGqlFilterSet
from .utils import generate_hidden_email


def only_me(func):
    def wrapper(root, info, *args, **kwargs):
        if root == info.context.user:
            return func(root, info, *args, **kwargs)
    return wrapper


def user_member_project_ids(current_user, owner=False):
    # Member in Projects
    project_ids = ProjectMembership.objects.filter(member=current_user).values('project')
    if owner:
        project_ids = project_ids.filter(role__type=ProjectRole.Type.PROJECT_OWNER)
        project_members = ProjectMembership.objects.filter(
            member__profile__deleted_at__isnull=True,  # Exclude already deleted users
            project__in=project_ids,
        ).order_by().values('project').annotate(
            member_count=models.Count('member', distinct=True),
        ).filter(member_count=1).values_list('project', 'project__title')
    else:
        project_members = ProjectMembership.objects.filter(
            ~models.Q(role__type=ProjectRole.Type.PROJECT_OWNER),
            member__profile__deleted_at__isnull=True,  # Exclude already deleted users
            project__in=project_ids,
        ).order_by().values('project').values_list('project', 'project__title')
    return [
        {
            'id': project_id,
            'title': project_title,
        } for project_id, project_title in project_members
    ]


class JwtTokenType(graphene.ObjectType):
    access_token = graphene.String()
    expires_in = graphene.String()


class UserFeatureAccessType(DjangoObjectType):
    class Meta:
        model = Feature
        only_fields = ('key', 'title', 'feature_type')


class UserProfileType(graphene.ObjectType):
    id = graphene.ID(required=True)
    display_name = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    display_picture_url = graphene.String()
    organization = graphene.String()

    @staticmethod
    def resolve_display_name(root, info, **kwargs) -> Union[str, None]:
        if root.deleted_at:
            return f'{settings.DELETED_USER_FIRST_NAME} {settings.DELETED_USER_LAST_NAME}'
        # root.user.first_name + root.user.last_name
        return root.get_display_name()

    @staticmethod
    def resolve_first_name(root, info, **kwargs) -> Union[str, None]:
        if root.deleted_at:
            return settings.DELETED_USER_FIRST_NAME
        return root.user.first_name

    @staticmethod
    def resolve_last_name(root, info, **kwargs) -> Union[str, None]:
        if root.deleted_at:
            return settings.DELETED_USER_LAST_NAME
        return root.user.last_name

    @staticmethod
    def resolve_display_picture_url(root, info, **kwargs) -> Union[str, None]:
        return info.context.request.build_absolute_uri(
            URLCachedFileField().to_representation(root.display_picture)
        )

    @staticmethod
    def resolve_organization(root, info, **kwargs) -> Union[str, None]:
        if root.deleted_at:
            return settings.DELETED_USER_ORGANIZATION
        return root.organization


class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = (
            'id', 'is_active',
        )

    email_display = graphene.String(required=True)
    profile = graphene.NonNull(UserProfileType)

    @staticmethod
    def resolve_email_display(root, info, **kwargs) -> Union[str, None]:
        return generate_hidden_email(root.email)

    @staticmethod
    def resolve_profile(root, info, **kwargs) -> Union[str, None]:
        return info.context.dl.user.profile.load(root.id)


class UserMeProjectType(graphene.ObjectType):
    id = graphene.String()
    title = graphene.String()


class UserMeType(DjangoObjectType):
    class Meta:
        model = User
        skip_registry = True
        only_fields = (
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
    email_opt_outs = graphene.List(graphene.NonNull(UserEmailConditionOptOutEnum))
    jwt_token = graphene.Field(JwtTokenType)
    last_active_project = graphene.Field('project.schema.ProjectDetailType')
    accessible_features = graphene.List(graphene.NonNull(UserFeatureAccessType), required=True)
    deleted_at = graphene.Date()
    sole_projects = graphene.List(UserMeProjectType)
    only_member_projects = graphene.List(UserMeProjectType)


    @staticmethod
    @only_me
    def resolve_display_picture(root, info, **kwargs) -> Union[str, None]:
        return root.profile.display_picture_id

    @staticmethod
    @only_me
    def resolve_display_picture_url(root, info, **kwargs) -> Union[str, None]:
        return info.context.request.build_absolute_uri(
            URLCachedFileField().to_representation(root.profile.display_picture)
        )

    @staticmethod
    @only_me
    def resolve_last_active_project(root, info, **kwargs) -> Union[int, None]:
        project = root.profile.last_active_project
        if project and project.get_current_user_role(info.context.user):
            return project
        # As a fallback return last created member project
        return Project.get_for_gq(info.context.user, only_member=True).order_by('-id').first()

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

    @staticmethod
    @only_me
    def resolve_accessible_features(root, info, **kwargs) -> Union[Feature, None]:
        return root.get_accessible_features()

    @staticmethod
    @only_me
    def resolve_deleted_at(root, info, **kwargs) -> Union[datetime.datetime.date, None]:
        return root.profile.deleted_at

    @staticmethod
    @only_me
    def resolve_sole_projects(root, info, **kwargs) -> Union[UserMeProjectType, None]:
        return user_member_project_ids(info.context.user, owner=True)

    @staticmethod
    @only_me
    def resolve_only_member_projects(root, info, **kwargs) -> Union[UserMeProjectType, None]:
        return user_member_project_ids(info.context.user)


class UserListType(CustomDjangoListObjectType):
    class Meta:
        model = User
        filterset_class = UserGqlFilterSet


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
