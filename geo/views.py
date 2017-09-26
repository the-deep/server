from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser

from deep.permissions import ModifyPermission

from .models import Region, AdminLevel  # , GeoShape
from .serializers import (
    RegionSerializer, AdminLevelSerializer,
    AdminLevelUploadSerializer
)


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          ModifyPermission]

    def get_queryset(self):
        return Region.get_for(self.request.user)


class AdminLevelViewSet(viewsets.ModelViewSet):
    """
    Admin Level API Point
    """
    serializer_class = AdminLevelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          ModifyPermission]

    def get_queryset(self):
        return AdminLevel.get_for(self.request.user)


class AdminLevelUploadViewSet(mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """
    Admin Level Upload API Point [Geo file]
    """
    serializer_class = AdminLevelUploadSerializer
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          ModifyPermission]

    def get_queryset(self):
        return AdminLevel.get_for(self.request.user)
