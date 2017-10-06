from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.views import TokenViewBase
from .serializers import (
    UserSerializer,
    HIDTokenObtainPairSerializer
)


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


class HIDTokenObtainPairView(TokenViewBase):
    """
    Takes a hid token for a user and returns an access and refresh JSON web
    token pair to prove the authentication of those hid token.
    """
    serializer_class = HIDTokenObtainPairSerializer
