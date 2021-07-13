from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import UserGroup
from .filters import UserGroupFilterSet


class UserGroupType(DjangoObjectType):
    class Meta:
        model = UserGroup
        fields = '__all__'

    def resolve_members(root, info):
        return info.context.dl_user_group_members.load(root.id)


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
