from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    """
    create:
    Register a new user

    retrieve:
    Get an existing user

    list:
    Get a list of all users

    destroy:
    Delete an existing user

    update:
    Modify an existing user

    partial_update:
    Modify an existing user partially
    """

    queryset = User.objects.all()  # .order_by('-date_joined)
    serializer_class = UserSerializer
    permission_classes = [UserPermission]
