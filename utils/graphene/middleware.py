from django.conf import settings
from project.change_log import ProjectChangeManager
from project.models import Project

from deep.exceptions import UnauthorizedException


class WhiteListMiddleware:
    """
    Graphql node whitelist for unauthenticated user
    """

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
        if info.field_name == "__schema" and not settings.DEBUG:
            return None
        return next(root, info, **args)


class ProjectLogMiddleware:
    """
    Middleware to track Project changes
    """

    WATCHED_PATH = [
        *[
            ["project", path]
            for path in [
                "projectUpdate",
                "projectDelete",
                "projectUserMembershipBulk",
                "projectUserGroupMembershipBulk",
                "projectRegionBulk",
                "projectVizConfigurationUpdate",
                "acceptRejectProject",
            ]
        ],
    ]

    def resolve(self, next, root, info, **args):
        if info.operation.operation == "mutation" and isinstance(root, Project) and info.path in self.WATCHED_PATH:
            with ProjectChangeManager(info.context.request, root.id):
                return next(root, info, **args)
        return next(root, info, **args)
