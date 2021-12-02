import graphene

from utils.common import has_select_related
from user.schema import UserType


class UserResourceMixin(graphene.ObjectType):
    created_at = graphene.DateTime(required=True)
    modified_at = graphene.DateTime(required=True)
    created_by = graphene.Field(UserType)
    modified_by = graphene.Field(UserType)

    def resolve_created_by(root, info, **kwargs):
        if has_select_related(root, 'created_by'):
            return root.created_by
        return info.context.dl.user_resource.created_by.load(root)

    def resolve_modified_by(root, info, **kwargs):
        if has_select_related(root, 'modified_by'):
            return root.modified_by
        return info.context.dl.user_resource.modified_by.load(root)
