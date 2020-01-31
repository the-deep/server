import logging
from rest_framework import permissions

from project.models import Project
from lead.models import Lead

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


class IsProjectMember(permissions.BasePermission):
    message = 'Only allowed for Project members'

    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        lead_id = view.kwargs.get('lead_id')

        if project_id and Project.get_for_member(request.user).filter(id=project_id).exists():
            return True
        elif lead_id and Lead.get_for(request.user).filter(id=lead_id).exists():
            return True
        return False
