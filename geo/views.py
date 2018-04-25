from django.conf import settings
from django.contrib.gis.gdal import Envelope
from django.core.serializers import serialize
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
from .models import Region, AdminLevel, GeoArea
from .serializers import (
    AdminLevelSerializer,
    RegionSerializer,
)

from geo.tasks import load_geo_areas
import json


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

        return response.Response(json.loads(serialize(
            'geojson',
            admin_level.geoarea_set.all(),
            geometry_field='polygons',
            fields=('pk', 'title', 'code', 'parent'),
        )))


class GeoBoundsView(views.APIView):
    """
    A view that returns geojson for given admin level
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, admin_level_id, version=None):
        if not AdminLevel.objects.filter(id=admin_level_id).exists():
            raise exceptions.NotFound()

        admin_level = AdminLevel.objects.get(id=admin_level_id)
        if not admin_level.can_get(request.user):
            raise exceptions.PermissionDenied()

        areas = admin_level.geoarea_set.filter(polygons__isnull=False)
        if areas.count() > 0:
            try:
                envelope = Envelope(*areas[0].polygons.extent)
                for area in areas[1:]:
                    envelope.expand_to_include(*area.polygons.extent)

                return response.Response({
                    'bounds': {
                        'min_x': envelope.min_x,
                        'min_y': envelope.min_y,
                        'max_x': envelope.max_x,
                        'max_y': envelope.max_y,
                    }
                })
            except ValueError as e:
                return response.Response({
                    'bounds': None,
                })

        return response.Response({
            'bounds': None,
        })


class GeoOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        regions = Region.objects.all()

        project = request.GET.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.can_get(request.user):
                raise exceptions.PermissionDenied()

            regions = regions.filter(project=project)

        regions = regions.distinct()
        result = {}
        for region in regions:
            result[str(region.id)] = [
                {
                    'label': '{} / {}'.format(geo_area.admin_level.title,
                                              geo_area.title),
                    'title': geo_area.title,
                    'key': str(geo_area.id),
                    'admin_level': geo_area.admin_level.level,
                    'admin_level_title': geo_area.admin_level.title,
                    'region': geo_area.admin_level.region.id,
                    'region_title': geo_area.admin_level.region.title,
                } for geo_area in GeoArea.objects.select_related(
                    'admin_level', 'admin_level__region',
                ).filter(
                    admin_level__region=region
                ).order_by('admin_level__level').distinct()
            ]

        return response.Response(result)
