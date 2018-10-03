from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

METHOD_ACTION_MAP = {
    'PUT': 'modify',
    'PATCH': 'modify',
    'GET': 'view',
    'POST': 'create',
    'DELETE': 'delete'
}


class ModifyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        action = METHOD_ACTION_MAP[request.method]
        objmethod = 'can_{}'.format(action)
        if hasattr(obj, objmethod):
            return getattr(obj, objmethod)(request.user)

        return obj.can_modify(request.user)


class IsSuperAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser
