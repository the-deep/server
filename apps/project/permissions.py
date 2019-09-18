from functools import reduce
from django.db import models
from rest_framework import permissions

from utils.data_structures import Dict

PROJECT_PERMISSIONS = Dict(
    lead=Dict(  # Dict is same as dict, can acccess elements by dot
        view=1 << 0,
        create=1 << 1,
        modify=1 << 2,
        delete=1 << 3,
        view_only_unprotected=1 << 4,
    ),
    entry=Dict({
        'view': 1 << 0,
        'create': 1 << 1,
        'modify': 1 << 2,
        'delete': 1 << 3,
        'view_only_unprotected': 1 << 4,
    }),
    setup=Dict({
        'modify': 1 << 0,
        'delete': 1 << 1,
    }),
    export=Dict({
        'create': 1 << 0
    }),
    assessment=Dict({
        'view': 1 << 0,
        'create': 1 << 1,
        'modify': 1 << 2,
        'delete': 1 << 3
    })
)


def get_project_permissions_value(item, actions=[]):
    """
    Return the numeric value of permission for actions related to the item
    E.g: get_permissions_value('lead', ['view', 'delete']) will return
    1 << 0 | 1 << 3
    """
    if actions == '__all__':
        # set all bits to 1
        return reduce(lambda a, e: a | e, PROJECT_PERMISSIONS[item].values())
    permissions = 0
    try:
        action_permissions = PROJECT_PERMISSIONS[item]
        for action in actions:
            permissions |= action_permissions[action]
    except Exception:
        return permissions
    return permissions


class JoinPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from project.models import ProjectJoinRequest
        # User should not already be a member
        # and there should not be existing request by this user
        # to this project (whether pending, accepted or rejected).
        return (
            not obj.is_member(request.user) and
            not ProjectJoinRequest.objects.filter(
                models.Q(status='pending') |
                models.Q(status='rejected'),
                project=obj,
                requested_by=request.user,
            ).exists()
        )


class AcceptRejectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from project.models import ProjectMembership, ProjectRole
        return ProjectMembership.objects.filter(
            project=obj,
            member=request.user,
            role__in=ProjectRole.get_admin_roles(),
        ).exists()


class MembershipModifyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from project.models import ProjectMembership
        if request.method in permissions.SAFE_METHODS:
            return True

        if not obj.role:
            return True

        project = obj.project
        user = ProjectMembership.objects.filter(
            project=project,
            member=request.user
        ).first()
        user_role = user and user.role

        if not user_role or user_role.level > obj.role.level:
            return False

        if not obj.role.is_creator_role:
            return True

        # If the user is the one with creator role, only let it
        # be changed if another membership with the creator role
        # exists.
        return ProjectMembership.objects.filter(
            ~models.Q(member=request.user),
            project=project,
            role=obj.role,
        ).exists()


def get_project_entities(Entity, user, action=None):
    """
    @Entity: classname for the entity
    @user: User instance
    @action: could be view, create, edit, delete, etc.
    """
    # TODO: camelcase to snakecase instead of just lower()
    item = Entity.__name__.lower()

    item_permissions = item + '_permissions'
    permission = PROJECT_PERMISSIONS.get(item, {}).get(action)
    if permission is None:
        return Entity.objects.none()

    fieldname = 'project__projectmembership__role__{}'.format(item_permissions)
    return Entity.objects.filter(
        project__projectmembership__member=user,
    ).annotate(
        new_permission_col=models.F(fieldname).bitand(permission)
    ).filter(
        new_permission_col=permission
    ).distinct()
