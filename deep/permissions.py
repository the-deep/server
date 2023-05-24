import logging
from typing import List
from enum import Enum, auto, unique
from collections import defaultdict

from django.db.models import F
from rest_framework import permissions

from deep.exceptions import PermissionDeniedException
from project.models import Project, ProjectRole, ProjectMembership
from analysis_framework.models import AnalysisFrameworkRole
from project.permissions import PROJECT_PERMISSIONS
from lead.models import Lead
from entry.models import Entry
from analysis.models import AnalysisPillar
from user_group.models import UserGroup, GroupMembership

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

    @classmethod
    def check_permission_from_serializer(cls, context, *perms):
        permissions = getattr(context, cls.CONTEXT_PERMISSION_ATTR)
        if permissions:
            return all([perm in permissions for perm in perms])


class ProjectPermissions(BasePermissions):

    @unique
    class Permission(Enum):
        # ---------------------- Project
        BASE_ACCESS = auto()
        UPDATE_PROJECT = auto()
        DELETE_PROJECT = auto()
        CAN_ADD_MEMBER = auto()
        # ---------------------- Unified Connector
        VIEW_UNIFIED_CONNECTOR = auto()
        CREATE_UNIFIED_CONNECTOR = auto()
        UPDATE_UNIFIED_CONNECTOR = auto()
        DELETE_UNIFIED_CONNECTOR = auto()
        # ---------------------- Lead
        CREATE_LEAD = auto()
        VIEW_ONLY_UNPROTECTED_LEAD = auto()
        VIEW_ALL_LEAD = auto()
        VIEW_ASSESSMENT_REGISTRY = auto()
        UPDATE_LEAD = auto()
        DELETE_LEAD = auto()
        # ---------------------- Entry
        CREATE_ENTRY = auto()
        VIEW_ENTRY = auto()
        UPDATE_ENTRY = auto()
        DELETE_ENTRY = auto()
        # ---------------------- Export
        CREATE_EXPORT = auto()
        # ---------------------- QA
        CAN_QUALITY_CONTROL = auto()
        # ---------------------- Analysis Module
        CREATE_ANALYSIS_MODULE = auto()

        # ---------------------AssessmentRegistry
        CREATE_ASSESSMENT_REGISTRY = auto()

    Permission.__name__ = 'ProjectPermission'

    __error_message__ = {
        Permission.UPDATE_PROJECT: "You don't have permission to update project",
        Permission.CAN_ADD_MEMBER: "You don't have permission to add member to project",
        Permission.CREATE_LEAD: "You don't have permission to create lead",
        Permission.VIEW_ONLY_UNPROTECTED_LEAD: "You don't have permission to view lead",
        Permission.VIEW_ALL_LEAD: "You don't have permission to view confidential lead",
        Permission.VIEW_ASSESSMENT_REGISTRY: "You don't have permission to view confidential assessment registry",
        Permission.UPDATE_LEAD: "You don't have permission to update lead",
        Permission.DELETE_LEAD: "You don't have permission to delete lead",
        Permission.CREATE_ENTRY: "You don't have permission to create entry",
        Permission.VIEW_ENTRY: "You don't have permission to view entry",
        Permission.UPDATE_ENTRY: "You don't have permission to update entry",
        Permission.DELETE_ENTRY: "You don't have permission to delete entry",
        Permission.CREATE_EXPORT: "You don't have permission to create exports",
        Permission.CAN_QUALITY_CONTROL: "You don't have permission to Quality Control",
        Permission.CREATE_ANALYSIS_MODULE: "You don't have permission to Analysis Module",
    }

    # NOTE: If we need to have delete permission as well make sure to update queryset in schema and mutations.
    READER_NON_CONFIDENTIAL = [
        Permission.BASE_ACCESS,
        Permission.VIEW_ENTRY,
        Permission.VIEW_ONLY_UNPROTECTED_LEAD,
        Permission.CREATE_EXPORT,
    ]
    READER = [
        Permission.BASE_ACCESS,
        Permission.VIEW_ENTRY,
        Permission.VIEW_ALL_LEAD,
        Permission.VIEW_ASSESSMENT_REGISTRY,
        Permission.CREATE_EXPORT,
    ]
    MEMBER = [
        *READER,
        Permission.CREATE_ENTRY,
        Permission.CREATE_LEAD,
        Permission.DELETE_ENTRY,
        Permission.DELETE_LEAD,
        Permission.UPDATE_ENTRY,
        Permission.UPDATE_LEAD,
        Permission.VIEW_ALL_LEAD,
        Permission.VIEW_ASSESSMENT_REGISTRY,
        Permission.VIEW_UNIFIED_CONNECTOR,
        Permission.CREATE_UNIFIED_CONNECTOR,
        Permission.UPDATE_UNIFIED_CONNECTOR,
        Permission.CREATE_ANALYSIS_MODULE,
        Permission.CREATE_ASSESSMENT_REGISTRY,
    ]
    ADMIN = [
        *MEMBER,
        Permission.UPDATE_PROJECT,
        Permission.CAN_ADD_MEMBER,
        Permission.DELETE_UNIFIED_CONNECTOR,
    ]
    PROJECT_OWNER = [
        *ADMIN,
        Permission.DELETE_PROJECT,
    ]

    PERMISSION_MAP = {
        ProjectRole.Type.PROJECT_OWNER: PROJECT_OWNER,
        ProjectRole.Type.ADMIN: ADMIN,
        ProjectRole.Type.MEMBER: MEMBER,
        ProjectRole.Type.READER: READER,
        ProjectRole.Type.READER_NON_CONFIDENTIAL: READER_NON_CONFIDENTIAL,
        ProjectRole.Type.UNKNOWN: [Permission.BASE_ACCESS],
    }
    BADGES_PERMISSION_MAP = {
        ProjectMembership.BadgeType.QA: Permission.CAN_QUALITY_CONTROL,
    }

    REVERSE_PERMISSION_MAP = defaultdict(list)
    for _role_type, _permissions in PERMISSION_MAP.items():
        for permission in _permissions:
            REVERSE_PERMISSION_MAP[permission].append(_role_type)
            REVERSE_PERMISSION_MAP[permission.value].append(_role_type)

    CONTEXT_PERMISSION_ATTR = 'project_permissions'

    @classmethod
    def get_permissions(cls, project, user) -> List[Permission]:
        role = project.get_current_user_role(user)
        badges = project.get_current_user_badges(user) or []
        if role is None:
            return []
        badges_permissions = [
            cls.BADGES_PERMISSION_MAP[badge]
            for badge in badges
            if badge in cls.BADGES_PERMISSION_MAP
        ]
        return [
            *cls.PERMISSION_MAP.get(role, []),
            *badges_permissions,
        ]


class AnalysisFrameworkPermissions(BasePermissions):

    @unique
    class Permission(Enum):
        CAN_ADD_USER = auto()
        CAN_CLONE_FRAMEWORK = auto()
        CAN_EDIT_FRAMEWORK = auto()
        CAN_USE_IN_OTHER_PROJECTS = auto()
        DELETE_FRAMEWORK = auto()

    Permission.__name__ = 'AnalysisFrameworkPermission'

    __error_message__ = {
        Permission.CAN_ADD_USER: "You don't have permission to add user",
        Permission.CAN_CLONE_FRAMEWORK: "You don't have permission to clone framework",
        Permission.CAN_EDIT_FRAMEWORK: "You don't have permission to edit framework",
        Permission.CAN_USE_IN_OTHER_PROJECTS: "You don't have permission to use in other projects",
    }

    DEFAULT = [  # NOTE: This is also send for public AF without membership
        Permission.CAN_CLONE_FRAMEWORK,
        Permission.CAN_USE_IN_OTHER_PROJECTS,
    ]
    EDITOR = [*DEFAULT, Permission.CAN_EDIT_FRAMEWORK]
    OWNER = [*EDITOR, Permission.CAN_ADD_USER]
    # Private roles (doesn't have clone permission)
    PRIVATE_VIEWER = [Permission.CAN_USE_IN_OTHER_PROJECTS]
    PRIVATE_EDITOR = [*PRIVATE_VIEWER, Permission.CAN_EDIT_FRAMEWORK]
    PRIVATE_OWNER = [*PRIVATE_EDITOR, Permission.CAN_ADD_USER]

    PERMISSION_MAP = {
        AnalysisFrameworkRole.Type.EDITOR: EDITOR,
        AnalysisFrameworkRole.Type.OWNER: OWNER,
        AnalysisFrameworkRole.Type.DEFAULT: DEFAULT,
        AnalysisFrameworkRole.Type.PRIVATE_EDITOR: PRIVATE_EDITOR,
        AnalysisFrameworkRole.Type.PRIVATE_OWNER: PRIVATE_OWNER,
        AnalysisFrameworkRole.Type.PRIVATE_VIEWER: PRIVATE_VIEWER,

    }

    CONTEXT_PERMISSION_ATTR = 'af_permissions'

    @classmethod
    def get_permissions(cls, role, is_public=False):
        if role is None and is_public:
            return cls.DEFAULT
        return cls.PERMISSION_MAP.get(role) or []


class UserGroupPermissions(BasePermissions):

    @unique
    class Permission(Enum):
        CAN_ADD_USER = auto()

    Permission.__name__ = 'UserGroupPermission'

    __error_message__ = {
        Permission.CAN_ADD_USER: "You don't have permission to update memberships",
    }

    ADMIN = [Permission.CAN_ADD_USER]
    NORMAL = []

    PERMISSION_MAP = {
        GroupMembership.Role.ADMIN: ADMIN,
        GroupMembership.Role.NORMAL: NORMAL,
    }

    CONTEXT_PERMISSION_ATTR = 'ug_permissions'

    @classmethod
    def get_permissions(cls, role):
        return cls.PERMISSION_MAP.get(role) or []
