from django.conf import settings
from django.db import models
from rest_framework import (
    exceptions,
    filters,
    permissions,
    response,
    status,
    views,
    viewsets,
)
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from project.models import Project
from .models import Region, AdminLevel
from .serializers import (
    AdminLevelSerializer,
    RegionSerializer,
)

from geo.tasks import load_geo_areas


class RegionFilterSet(UserResourceFilterSet):
    """
    Region filter set

    Filter by code, title and public fields
    """
    class Meta:
        model = Region
        fields = ['id', 'code', 'title', 'public', 'project',
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


class RegionCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, region_id, version=None):
        if not Region.objects.filter(id=region_id).exists():
            raise exceptions.NotFound()

        region = Region.objects.get(id=region_id)
        if not region.can_get(request.user):
            raise exceptions.PermissionDenied()

        new_region = region.clone_to_private(request.user)
        serializer = RegionSerializer(new_region, context={'request': request})

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.can_modify(request.user):
                raise exceptions.ValidationError({
                    'project': 'Invalid project',
                })
            project.regions.remove(region)
            project.regions.add(new_region)

        return response.Response(serializer.data,
                                 status=status.HTTP_201_CREATED)


class AdminLevelFilterSet(django_filters.rest_framework.FilterSet):
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


class GeoAreasLoadTriggerView(views.APIView):
    """
    A trigger for loading geo areas from admin level
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, region_id, version=None):
        if not Region.objects.filter(id=region_id).exists():
            raise exceptions.NotFound()

        if not Region.objects.get(id=region_id).can_get(request.user):
            raise exceptions.PermissionDenied()

        if not settings.TESTING:
            load_geo_areas.delay(region_id)

        return response.Response({
            'load_triggered': region_id,
        })


class GeoJsonView(views.APIView):
    """
    A view that returns geojson for given admin level
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, admin_level_id, version=None):
        # TODO: Use get_object_or_404

        if not AdminLevel.objects.filter(id=admin_level_id).exists():
            raise exceptions.NotFound()

        admin_level = AdminLevel.objects.get(id=admin_level_id)
        if not admin_level.can_get(request.user):
            raise exceptions.PermissionDenied()

        if not admin_level.geojson:
            admin_level.calc_cache()

        return response.Response(admin_level.geojson)


class GeoBoundsView(views.APIView):
    """
    A view that returns geo bounds for given admin level
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, admin_level_id, version=None):
        if not AdminLevel.objects.filter(id=admin_level_id).exists():
            raise exceptions.NotFound()

        admin_level = AdminLevel.objects.get(id=admin_level_id)
        if not admin_level.can_get(request.user):
            raise exceptions.PermissionDenied()

        if not admin_level.bounds:
            admin_level.calc_cache()

        return response.Response({
            'bounds': admin_level.bounds
        })


class GeoOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        regions = Region.objects.all()

        project = request.GET.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.is_member(request.user):
                raise exceptions.PermissionDenied()

            regions = regions.filter(project=project)

        regions = regions.distinct()
        result = {}
        for region in regions:
            if not region.geo_options:
                region.calc_cache()
            result[str(region.id)] = region.geo_options

        return response.Response(result)
