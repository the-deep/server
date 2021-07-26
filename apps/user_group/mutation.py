import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
    DeleteMutation,
)

from .models import UserGroup
from .schema import UserGroupType
from .serializers import UserGroupGqSerializer as UserGroupSerializer


UserGroupInputType = generate_input_type_for_serializer(
    'UserGroupInputType',
    serializer_class=UserGroupSerializer,
)


class CreateUserGroup(GrapheneMutation):
    class Arguments:
        data = UserGroupInputType(required=True)
    model = UserGroup
    serializer_class = UserGroupSerializer
    result = graphene.Field(UserGroupType)
    permissions = []  # TODO: Add permission check and test


class UpdateUserGroup(GrapheneMutation):
    class Arguments:
        data = UserGroupInputType(required=True)
        id = graphene.ID(required=True)
    model = UserGroup
    serializer_class = UserGroupSerializer
    result = graphene.Field(UserGroupType)
    permissions = []  # TODO: Add permission check and test


class DeleteUserGroup(DeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = UserGroup
    result = graphene.Field(UserGroupType)
    permissions = []  # TODO: Add permission check and test


class Mutation():
    user_group_create = CreateUserGroup.Field()
    user_group_update = UpdateUserGroup.Field()
    user_group_delete = DeleteUserGroup.Field()
