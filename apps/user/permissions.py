from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    def _is_authenticated(self, rq):
        return rq.user.is_authenticated

    def has_permission(self, request, view):
        if self._is_authenticated(request) or view.action == 'create':
            # NOTE:for create user using same api, so return True for `create`
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if self._is_authenticated(request) and request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user
