from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .serializers import (
    UserSerializer,
)
from docs.registrar import register_for_docs


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


@register_for_docs
class UserViewSet(viewsets.ModelViewSet):
    """
    create:
    Register a new user

    retrieve:
    Get an existing user

    list:
    Get a list of all users ordered by date joined

    destroy:
    Delete an existing user

    update:
    Modify an existing user

    partial_update:
    Modify an existing user partially
    """

    queryset = User.objects.all()\
        .order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    def get_object(self):
        pk = self.kwargs['pk']
        if pk == 'me':
            return self.request.user
        else:
            return super().get_object()
