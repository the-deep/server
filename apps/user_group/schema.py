import graphene

from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import UserGroup, GroupMembership
from .filters import UserGroupFilterSet
from .enums import GroupMembershipRoleEnum


class GroupMembershipType(DjangoObjectType):
    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'joined_at', 'added_by',)

    role = graphene.Field(GroupMembershipRoleEnum, required=True)
    role_display = EnumDescription(source='get_role_display', required=True)


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

    current_user_role = graphene.Field(GroupMembershipRoleEnum)
    current_user_role_display = EnumDescription(source='get_current_user_role_display')

    @staticmethod
    def resolve_current_user_role(root, info):
        return info.context.dl.user_group.current_user_role.load(root.id)


class UserGroupDetailType(UserGroupType):
    class Meta:
        model = UserGroup
        skip_registry = True
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

    @staticmethod
    def resolve_memberships(root, info):
        return info.context.dl.user_group.memberships.load(root.id)


class UserGroupListType(CustomDjangoListObjectType):
    class Meta:
        model = UserGroup
        filterset_class = UserGroupFilterSet


class Query:
    user_group = DjangoObjectField(UserGroupDetailType)
    user_groups = DjangoPaginatedListObjectField(
        UserGroupListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
