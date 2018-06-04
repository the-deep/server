from rest_framework import permissions


class JoinPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from project.models import ProjectJoinRequest
        # User should not already be a member
        # and there should not be existing request by this user
        # to this project (whether pending, accepted or rejected).
        return (
            not obj.is_member(request.user) and
            not ProjectJoinRequest.objects.filter(
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
