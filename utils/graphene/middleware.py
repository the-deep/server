from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.translation import gettext

PERMISSION_DENIED_MESSAGE = 'You do not have permission to perform this action.'


class WhiteListMiddleware:
    '''
    Graphql node whitelist for unauthenticated user
    '''
    def resolve(self, next, root, info, **args):
        # if user is not authenticated and user is not accessing
        # whitelisted nodes, then raise permission denied error

        # furthermore, this check must only happen in the root node, and not in deeper nodes
        if root is None:
            if not info.context.user.is_authenticated and info.field_name not in settings.GRAPHENE_NODES_WHITELIST:
                raise PermissionDenied(gettext(PERMISSION_DENIED_MESSAGE))
        return next(root, info, **args)


class DisableIntrospectionSchemaMiddleware:
    """
    This middleware should be used in production.
    """
    def resolve(self, next, root, info, **args):
        if info.field_name == '__schema':
            return None
        return next(root, info, **args)
