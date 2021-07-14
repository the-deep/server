import graphene

from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import UserGroup, GroupMembership
from .filters import UserGroupFilterSet


class GroupMembershipType(DjangoObjectType):
    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'role', 'joined_at', 'added_by',)


class UserGroupType(DjangoObjectType):
    class Meta:
        model = UserGroup
        fields = (
            'id',
            'title',
            'description',
            'created_at',
            'created_by',
            'modified_at',
            'modified_by',
            'client_id',
            'custom_project_fields',
            'global_crisis_monitoring',
        )

    memberships = DjangoListField(GroupMembershipType)
    current_user_role = graphene.String()

    def resolve_memberships(root, info):
        return info.context.dl.user_group.memberships.load(root.id)

    def resolve_current_user_role(root, info):
        return info.context.dl.user_group.current_user_role.load(root.id)


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
