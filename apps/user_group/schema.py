import graphene

from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import UserGroup, GroupMembership
from .filters import UserGroupGQFilterSet
from .enums import GroupMembershipRoleEnum


class GroupMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = GroupMembership
        only_fields = (
            'id', 'member', 'joined_at', 'added_by',
        )

    role = graphene.Field(GroupMembershipRoleEnum, required=True)
    role_display = EnumDescription(source='get_role_display', required=True)


class UserGroupType(DjangoObjectType):
    class Meta:
        model = UserGroup
        only_fields = (
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
    memberships_count = graphene.Int(required=True)
    memberships = DjangoListField(GroupMembershipType)

    @staticmethod
    def resolve_current_user_role(root, info):
        return info.context.dl.user_group.current_user_role.load(root.id)

    @staticmethod
    def resolve_memberships(root, info):
        # Only for groups with current user as members are fetched. (Logic in dataloader)
        return info.context.dl.user_group.memberships.load(root.id)

    @staticmethod
    def resolve_memberships_count(root, info):
        return info.context.dl.user_group.memberships_count.load(root.id)


class UserGroupListType(CustomDjangoListObjectType):
    class Meta:
        model = UserGroup
        filterset_class = UserGroupGQFilterSet


class Query:
    user_group = DjangoObjectField(UserGroupType)
    user_groups = DjangoPaginatedListObjectField(
        UserGroupListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
