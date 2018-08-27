from rest_framework import permissions

from project.models import ProjectMembership
from project.permissions import PROJECT_PERMISSIONS

import logging

logger = logging.getLogger(__name__)

METHOD_ACTION_MAP = {
    'PUT': 'modify',
    'GET': 'view',
    'POST': 'create',
    'DELETE': 'delete'
}


class ModifyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.can_modify(request.user)


class IsSuperAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser


class ProjectEntityPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        project = obj.get_project()
        action = METHOD_ACTION_MAP(request.method)
        item = obj.__class__.__name__.lower()

        if not project.is_member(request.user):
            return False

        membership = ProjectMembership.objects.get(
            project=project,
            member=request.user
        )
        role = membership.role

        user_permissions = getattr(role, item + '_permissions')
        permission = PROJECT_PERMISSIONS.get(item, {}).get(action)
        return permission is not None \
            and user_permissions & permission > 0
