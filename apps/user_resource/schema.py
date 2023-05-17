import graphene

from graphql.execution.base import ResolveInfo
from django.db import models

from utils.common import has_select_related
from user.schema import UserType


class UserResourceMixin(graphene.ObjectType):
    created_at = graphene.DateTime(required=True)
    modified_at = graphene.DateTime(required=True)
    created_by = graphene.Field(UserType)
    modified_by = graphene.Field(UserType)

    def resolve_created_by(root, info, **kwargs):
        return resolve_user_field(root, info, 'created_by')

    def resolve_modified_by(root, info, **kwargs):
        return resolve_user_field(root, info, 'modified_by')


def resolve_user_field(root: models.Model, info: ResolveInfo, field: str):
    # Check if it is already fetched.
    if has_select_related(root, field):
        return getattr(root, field)
    # Use Dataloader to load the data
    return info.context.dl.user.users.load(
        getattr(root, f"{field}_id"),  # Pass ID to dataloader
    )
