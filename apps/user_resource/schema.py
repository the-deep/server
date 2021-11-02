import graphene

from user.schema import UserType


class UserResourceMixin(graphene.ObjectType):
    created_at = graphene.DateTime(required=True)
    modified_at = graphene.DateTime(required=True)
    created_by = graphene.Field(UserType)
    modified_by = graphene.Field(UserType)
