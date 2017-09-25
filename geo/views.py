from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Region, AdminLevel  # , GeoShape
from .serializers import (
    RegionSerializer, AdminLevelSerializer,
    AdminLevelUploadSerializer
)


class RegionViewSet(viewsets.ModelViewSet):
    """
    TODO: is_global only for acaps admins
    TODO: Add permissions for related project admins
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AdminLevelViewSet(viewsets.ModelViewSet):
    """
    Admin Level API Point
    """
    queryset = AdminLevel.objects.all()
    serializer_class = AdminLevelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AdminLevelUploadViewSet(mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """
    Admin Level Upload API Point [Geo file]
    """
    queryset = AdminLevel.objects.all()
    serializer_class = AdminLevelUploadSerializer
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
