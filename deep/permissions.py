import logging
from django.db.models import F
from rest_framework import permissions

from project.models import Project, ProjectRole
from project.permissions import PROJECT_PERMISSIONS
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


class CreateLeadPermission(permissions.BasePermission):
    """Permission class to check if user can create Lead"""
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        # Check project and all
        project_id = request.data['project']
        # If there is no project id, the serializers will give 400 error, no need to forbid here
        if project_id is None:
            return True

        create_lead_perm_value = PROJECT_PERMISSIONS.lead.create
        return ProjectRole.objects.annotate(
            create_lead=F('lead_permissions').bitand(create_lead_perm_value)
        ).filter(
            projectmembership__project_id=project_id,
            projectmembership__member=request.user,
            create_lead__gt=0,
        ).exists()


class CreateEntryPermission(permissions.BasePermission):
    """Permission class to check if user can create Lead"""
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        # Check project and all
        project_id = request.data['project']
        # If there is no project id, the serializers will give 400 error, no need to forbid here
        if project_id is None:
            return True

        create_entry_perm_value = PROJECT_PERMISSIONS.entry.create
        return ProjectRole.objects.annotate(
            create_entry=F('entry_permissions').bitand(create_entry_perm_value)
        ).filter(
            projectmembership__project_id=project_id,
            projectmembership__member=request.user,
            create_entry__gt=0,
        ).exists()


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
