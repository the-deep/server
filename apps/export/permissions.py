from rest_framework import permissions


class ExportViewSetPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if (view.action in ('list', 'update', 'destroy') or (request.user and request.user.is_authenticated)):
            return True
        return False
