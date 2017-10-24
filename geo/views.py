from django.db import models
from rest_framework import mixins, viewsets, permissions, filters
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from .models import Region, AdminLevel  # , GeoShape
from .serializers import (
    RegionSerializer, AdminLevelSerializer,
    AdminLevelUploadSerializer,
)


class RegionFilterSet(UserResourceFilterSet):
    """
    Region filter set

    Filter by code, title and public fields
    """
    class Meta:
        model = Region
        fields = ['id', 'code', 'title', 'public',
                  'created_at', 'created_by', 'modified_at', 'modified_by']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = RegionFilterSet
    search_fields = ('title', 'code')

    def get_queryset(self):
        return Region.get_for(self.request.user)


class AdminLevelFilterSet(filters.FilterSet):
    """
    AdminLevel filter set

    Filter by title, region and parent
    """
    class Meta:
        model = AdminLevel
        fields = ['id', 'title', 'region', 'parent']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class AdminLevelViewSet(viewsets.ModelViewSet):
    """
    Admin Level API Point
    """
    serializer_class = AdminLevelSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = AdminLevelFilterSet
    search_fields = ('title')

    def get_queryset(self):
        return AdminLevel.get_for(self.request.user)


class AdminLevelUploadViewSet(mixins.UpdateModelMixin,
                              viewsets.GenericViewSet):
    """
    Admin Level Upload API Point [Geo file]
    """
    serializer_class = AdminLevelUploadSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AdminLevel.get_for(self.request.user)
