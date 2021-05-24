import logging
from django.db.models import F
from rest_framework import permissions

from project.models import Project, ProjectRole
from project.permissions import PROJECT_PERMISSIONS
from lead.models import Lead
from entry.models import Entry
from analysis.models import AnalysisPillar

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
        project_id = request.data.get('project')

        # If there is no project id, the serializers will give 400 error, no need to forbid here
        if project_id is None:
            return True

        # Since this supports list value for project
        if isinstance(project_id, list):
            project_ids = set(project_id)
        else:
            project_ids = {project_id}

        create_lead_perm_value = PROJECT_PERMISSIONS.lead.create

        # Check if the user has create permissions on all projects
        # To do this, filter projects in which user has permissions and check if
        # the returned result length equals the queried projects length
        projects_count = Project.objects.filter(
            id__in=project_ids,
            projectmembership__member=request.user
        ).annotate(
            create_lead=F('projectmembership__role__lead_permissions').bitand(create_lead_perm_value)
        ).filter(
            create_lead__gt=0,
        ).count()

        return projects_count == len(project_ids)


class DeleteLeadPermission(permissions.BasePermission):
    """Checks if user can delete lead(s)"""
    def has_permission(self, request, view):
        if request.method not in ('POST', 'DELETE'):
            return True

        project_id = view.kwargs.get('project_id')

        if not project_id:
            return False

        delete_lead_perm_value = PROJECT_PERMISSIONS.lead.delete

        # Check if the user has delete permissions on all projects
        return Project.objects.filter(
            id=project_id,
            projectmembership__member=request.user
        ).annotate(
            delete_lead=F('projectmembership__role__lead_permissions').bitand(delete_lead_perm_value)
        ).filter(
            delete_lead__gt=0,
        ).exists()


class CreateEntryPermission(permissions.BasePermission):
    """Permission class to check if user can create Lead"""
    def get_project_id(self, request):
        """Try getting project id first from the data itself, if not try to
        get it from lead
        """
        project_id = request.data.get('project')
        if project_id:
            return project_id
        # Else, get it from lead
        lead = Lead.objects.filter(id=request.data.get('lead')).first()
        return lead and lead.project.id

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        # Get project id from request
        project_id = self.get_project_id(request)

        # If there is no project id, probably lead does not exist
        if project_id is None:
            return False

        create_entry_perm_value = PROJECT_PERMISSIONS.entry.create
        return ProjectRole.objects.annotate(
            create_entry=F('entry_permissions').bitand(create_entry_perm_value)
        ).filter(
            projectmembership__project_id=project_id,
            projectmembership__member=request.user,
            create_entry__gt=0,
        ).exists()


class CreateAssessmentPermission(permissions.BasePermission):
    """Permission class to check if user can create Lead"""
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        # Check project and all
        project_id = request.data.get('project')
        # If there is no project id, the serializers will give 400 error, no need to forbid here
        if project_id is None:
            return True

        create_assmt_perm_value = PROJECT_PERMISSIONS.assessment.create
        return ProjectRole.objects.annotate(
            create_entry=F('assessment_permissions').bitand(create_assmt_perm_value)
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
        entry_id = view.kwargs.get('entry_id')
        analysis_pillar_id = view.kwargs.get('analysis_pillar_id')

        if project_id:
            return Project.get_for_member(request.user).filter(id=project_id).exists()
        elif lead_id:
            return Lead.get_for(request.user).filter(id=lead_id).exists()
        elif entry_id:
            return Entry.get_for(request.user).filter(id=entry_id).exists()
        elif analysis_pillar_id:
            return AnalysisPillar.objects.filter(
                analysis__project__projectmembership__member=request.user,
                id=analysis_pillar_id
            ).exists()
        return True

    def has_object_permission(self, request, view, obj):
        if type(obj) == Project:
            return obj.members.filter(id=request.user.id).exists()
        return True
