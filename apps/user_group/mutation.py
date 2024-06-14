import graphene
from django.core.exceptions import PermissionDenied
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from deep.permissions import UserGroupPermissions as UgP
from utils.graphene.mutation import (
    GrapheneMutation,
    UserGroupBulkGrapheneMutation,
    UserGroupDeleteMutation,
    UserGroupGrapheneMutation,
    generate_input_type_for_serializer,
)

from .models import GroupMembership, UserGroup
from .schema import GroupMembershipType, UserGroupType
from .serializers import UserGroupGqSerializer, UserGroupMembershipGqlSerializer

UserGroupInputType = generate_input_type_for_serializer(
    "UserGroupInputType",
    serializer_class=UserGroupGqSerializer,
)

UserGroupMembershipInputType = generate_input_type_for_serializer(
    "UserGroupMembershipInputType",
    serializer_class=UserGroupMembershipGqlSerializer,
)


class CreateUserGroup(GrapheneMutation):
    class Arguments:
        data = UserGroupInputType(required=True)

    model = UserGroup
    serializer_class = UserGroupGqSerializer
    result = graphene.Field(UserGroupType)

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to create AF


class UpdateUserGroup(UserGroupGrapheneMutation):
    class Arguments:
        data = UserGroupInputType(required=True)

    result = graphene.Field(UserGroupType)
    # class vars
    serializer_class = UserGroupGqSerializer
    model = UserGroup

    @classmethod
    def check_permissions(cls, info, **_):
        if info.context.user != info.context.active_ug.created_by:
            raise PermissionDenied("Only creater have permission to update user group")

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        kwargs["id"] = info.context.active_ug.id
        return super().perform_mutate(root, info, **kwargs)


class DeleteUserGroup(UserGroupDeleteMutation):
    result = graphene.Field(UserGroupType)
    # class vars
    model = UserGroup

    @classmethod
    def check_permissions(cls, info, **_):
        if info.context.user != info.context.active_ug.created_by:
            raise PermissionDenied("Only creater have permission to delete user group")

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        kwargs["id"] = info.context.active_ug.id
        return super().perform_mutate(root, info, **kwargs)


class BulkUserGroupMembershipInputType(UserGroupMembershipInputType):
    id = graphene.ID()


class BulkUpdateUserGroupMembership(UserGroupBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkUserGroupMembershipInputType))
        delete_ids = graphene.List(graphene.NonNull(graphene.ID))

    result = graphene.List(GroupMembershipType)
    deleted_result = graphene.List(graphene.NonNull(GroupMembershipType))
    # class vars
    serializer_class = UserGroupMembershipGqlSerializer
    model = GroupMembership
    permissions = [UgP.Permission.CAN_ADD_USER]

    @classmethod
    def get_valid_delete_items(cls, info, delete_ids):
        ug = info.context.active_ug
        return GroupMembership.objects.filter(
            pk__in=delete_ids,  # id's provided
            group=ug,  # For active user group
        ).exclude(
            # Exclude yourself and owner of the user group
            member__in=[info.context.user, ug.created_by]
        )


class UserGroupMutationType(DjangoObjectType):
    """
    This mutation is for other scoped objects
    """

    user_group_update = UpdateUserGroup.Field()
    user_group_delete = DeleteUserGroup.Field()
    user_group_membership_bulk = BulkUpdateUserGroupMembership.Field()

    class Meta:
        model = UserGroup
        skip_registry = True
        fields = ("id", "title")

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            user_group = UserGroup.get_for_gq(info.context.user, only_member=True).get(pk=id)
            info.context.set_active_usergroup(user_group)
            return user_group
        except UserGroup.DoesNotExist:
            raise PermissionDenied()


class Mutation:
    user_group_create = CreateUserGroup.Field()
    user_group = DjangoObjectField(UserGroupMutationType)
