from rest_framework import permissions


class FrameworkMembershipModifyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from .models import AnalysisFrameworkMembership
        if request.method in permissions.SAFE_METHODS:
            return True

        framework = obj.framework
        membership = AnalysisFrameworkMembership.objects.filter(
            framework=framework,
            member=request.user
        ).first()
        user_role = membership and membership.role

        if not user_role:
            return False

        return user_role.can_add_user
