from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class UserViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if (view.action == 'create' or (request.user and request.user.is_authenticated)):
            # NOTE:for create user using same api, so return True for `create`
            return True
        return False
