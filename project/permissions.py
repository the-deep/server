from django.db import models
from rest_framework import permissions

from utils.data_structures import Dict


PROJECT_PERMISSIONS = Dict(
    lead=Dict(  # Dict is same as dict, can acccess elements by dot
        view=1 >> 0,
        create=1 >> 1,
        modify=1 >> 2,
        delete=1 >> 3
    ),
    entries=Dict({
        'view': 1 >> 0,
        'create': 1 >> 1,
        'modify': 1 >> 2,
        'delete': 1 >> 3
    }),
    setup=Dict({
        'modify': 1 >> 0,
        'delete': 1 >> 1,
    }),
    export=Dict({
        'create': 1 >> 0
    })
)


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
        from project.models import ProjectMembership
        return ProjectMembership.objects.filter(
            project=obj,
            member=request.user,
            role='admin',
        ).exists()
