import logging
from enum import Enum, auto, unique

from django.db.models import F
from rest_framework import permissions

from deep.exceptions import PermissionDeniedException
from project.models import Project, ProjectRole
from project.permissions import PROJECT_PERMISSIONS
from lead.models import Lead
from entry.models import Entry
from analysis.models import AnalysisPillar
from user_group.models import UserGroup

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


class IsUserGroupMember(permissions.BasePermission):
    message = 'Only allowed for UserGroup members'

    def has_permission(self, request, view):
        user_group_id = view.kwargs.get('pk')
        if user_group_id:
            return UserGroup.get_for_member(request.user).filter(id=user_group_id).exists()
        return True


# ---------------------------- GRAPHQL Permissions ------------------------------

class BasePermissions():

    # ------------ Define this after using this as base -----------
    @unique
    class Permission(Enum):
        pass
    __error_message__ = {}
    PERMISSION_MAP = {}
    CONTEXT_PERMISSION_ATTR = ''
    # ------------ Define this after using this as base -----------

    DEFAULT_PERMISSION_DENIED_MESSAGE = PermissionDeniedException.default_message

    @classmethod
    def get_permissions(cls, role):
        return cls.PERMISSION_MAP.get(role) or []

    @classmethod
    def get_permission_message(cls, permission):
        return cls.__error_message__.get(permission, cls.DEFAULT_PERMISSION_DENIED_MESSAGE)

    @classmethod
    def check_permission(cls, info, *perms):
        permissions = getattr(info.context, cls.CONTEXT_PERMISSION_ATTR)
        if permissions:
            return all([perm in permissions for perm in perms])


class ProjectPermissions(BasePermissions):

    @unique
    class Permission(Enum):
        # ---------------------- Project
        UPDATE_PROJECT = auto()
        # ---------------------- Lead
        CREATE_LEAD = auto()
        VIEW_ONLY_UNPROTECTED_LEAD = auto()
        VIEW_ALL_LEAD = auto()
        UPDATE_LEAD = auto()
        DELETE_LEAD = auto()
        # ---------------------- Entry
        CREATE_ENTRY = auto()
        VIEW_ONLY_UNPROTECTED_ENTRY = auto()
        VIEW_ALL_ENTRY = auto()
        UPDATE_ENTRY = auto()
        DELETE_ENTRY = auto()

    __error_message__ = {
        Permission.UPDATE_PROJECT: "You don't have permission to update project",
        Permission.CREATE_LEAD: "You don't have permission to create lead",
        Permission.VIEW_ONLY_UNPROTECTED_LEAD: "You don't have permission to view lead",
        Permission.VIEW_ALL_LEAD: "You don't have permission to view confidential lead",
        Permission.UPDATE_LEAD: "You don't have permission to update lead",
        Permission.DELETE_LEAD: "You don't have permission to delete lead",
        Permission.CREATE_ENTRY: "You don't have permission to create entry",
        Permission.VIEW_ONLY_UNPROTECTED_ENTRY: "You don't have permission to view entry",
        Permission.VIEW_ALL_ENTRY: "You don't have permission to view confidential entry",
        Permission.UPDATE_ENTRY: "You don't have permission to update entry",
        Permission.DELETE_ENTRY: "You don't have permission to delete entry",
    }

    VIEWER_NON_CONFIDENTIAL = [
        Permission.VIEW_ONLY_UNPROTECTED_ENTRY,
        Permission.VIEW_ONLY_UNPROTECTED_LEAD,
    ]
    VIEWER = [
        Permission.VIEW_ALL_ENTRY,
        Permission.VIEW_ALL_LEAD,
    ]
    READER_NON_CONFIDENTIAL = [
        *VIEWER_NON_CONFIDENTIAL,
        # Add export permission here
    ]
    READER = [
        *VIEWER,
        # Add export permission here
    ]
    SOURCER = [
        Permission.CREATE_LEAD,
        Permission.VIEW_ALL_LEAD,
        Permission.UPDATE_LEAD,
        Permission.DELETE_LEAD,
    ]
    ANALYST = [
        *READER,
        Permission.CREATE_LEAD,
        Permission.UPDATE_LEAD,
        Permission.DELETE_LEAD,
        Permission.CREATE_ENTRY,
        Permission.UPDATE_ENTRY,
        Permission.DELETE_ENTRY,
    ]
    ADMIN = [*ANALYST]
    CLAIRVOYANT_ONE = [*ADMIN]

    # NOTE: Key are already defined in production.
    # TODO: Will need to create this role locally to work.
    PERMISSION_MAP = {
        'Viewer (Non Confidential)': VIEWER_NON_CONFIDENTIAL,
        'Viewer': VIEWER,
        'Reader (Non Confidential)': READER_NON_CONFIDENTIAL,
        'Reader': READER,
        'Sourcer': SOURCER,
        'Analyst': ANALYST,
        'Admin': ADMIN,
        'Clairvoyant One': CLAIRVOYANT_ONE,
    }

    CONTEXT_PERMISSION_ATTR = 'project_permissions'


class AnalysisFrameworkPermissions(BasePermissions):

    @unique
    class Permission(Enum):
        CAN_ADD_USER = auto()
        CAN_CLONE_FRAMEWORK = auto()
        CAN_EDIT_FRAMEWORK = auto()
        CAN_USE_IN_OTHER_PROJECTS = auto()
        DELETE_FRAMEWORK = auto()

    __error_message__ = {
        Permission.CAN_ADD_USER: "You don't have permission to add user",
        Permission.CAN_CLONE_FRAMEWORK: "You don't have permission to clone framework",
        Permission.CAN_EDIT_FRAMEWORK: "You don't have permission to edit framework",
        Permission.CAN_USE_IN_OTHER_PROJECTS: "You don't have permission to use in other projects",
    }

    DEFAULT = [
        Permission.CAN_CLONE_FRAMEWORK,
        Permission.CAN_USE_IN_OTHER_PROJECTS,
    ]
    EDITOR = [*DEFAULT, Permission.CAN_EDIT_FRAMEWORK]
    OWNER = [*EDITOR, Permission.CAN_ADD_USER]
    # Private roles (doesn't have clone permission)
    PRIVATE_VIEWER = [Permission.CAN_USE_IN_OTHER_PROJECTS]
    PRIVATE_EDITOR = [*PRIVATE_VIEWER, Permission.CAN_EDIT_FRAMEWORK]
    PRIVATE_OWNER = [*PRIVATE_EDITOR, Permission.CAN_ADD_USER]

    # NOTE: Key are already defined in production.
    # TODO: Will need to create this role locally to work.
    PERMISSION_MAP = {
        'Editor': EDITOR,
        'Owner': OWNER,
        'Default': DEFAULT,
        'Private Editor': PRIVATE_EDITOR,
        'Private Owner': PRIVATE_OWNER,
        'Private Viewer': PRIVATE_VIEWER,

    }

    CONTEXT_PERMISSION_ATTR = 'af_permissions'
