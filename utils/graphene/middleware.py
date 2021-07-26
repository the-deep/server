from django.conf import settings
from deep.exceptions import UnauthorizedException


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
                raise UnauthorizedException
        return next(root, info, **args)


class DisableIntrospectionSchemaMiddleware:
    """
    This middleware disables request with __schema in production.
    """
    def resolve(self, next, root, info, **args):
        if info.field_name == '__schema' and not settings.DEBUG:
            return None
        return next(root, info, **args)
