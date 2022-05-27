from django.shortcuts import redirect
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal.error import GDALException
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
from rest_framework.decorators import action
import django_filters

from deep.permissions import (
    ModifyPermission,
    IsProjectMember
)
from project.models import Project
from project.tasks import generate_project_geo_region_cache

from .models import Region, AdminLevel, GeoArea
from .serializers import (
    AdminLevelSerializer,
    RegionSerializer,
    GeoAreaSerializer
)
from .filter_set import (
    GeoAreaFilterSet,
    AdminLevelFilterSet,
    RegionFilterSet
)
from .tasks import load_geo_areas


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = RegionFilterSet
    search_fields = ('title', 'code')

    def get_queryset(self):
        return Region.get_for(self.request.user).defer('geo_options')

    @action(
        detail=True,
        url_path='intersects',
        methods=('post',),
        # TODO: Better permissions
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_intersects(self, request, pk=None, version=None):
        region = self.get_object()
        try:
            geoms = []
            features = request.data['features']
            for feature in features:
                geoms.append([feature.get('id'), GEOSGeometry(str(feature['geometry']))])
        except (GDALException, KeyError) as e:
            raise exceptions.ValidationError(
                f"Geometry parsed failed, Error: {getattr(e, 'message', repr(e))}"
            )
        return response.Response([
            {
                'id': id,
                'region_id': region.pk,
                'geoareas': (
                    # https://docs.djangoproject.com/en/2.1/ref/contrib/gis/geoquerysets/
                    GeoArea.objects.filter(
                        admin_level__region=region,
                        polygons__intersects=geom,
                    ).values_list('id', flat=True)
                ),
            }
            for id, geom in geoms
        ])

    @action(
        detail=True,
        url_path='publish',
        methods=['post'],
        serializer_class=RegionSerializer,
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_published(self, request, pk=None, version=None):
        region = self.get_object()
        if not region.can_publish(self.request.user):
            raise exceptions.ValidationError('Can be published by user who created it')
        region.is_published = True
        region.save(update_fields=['is_published'])
        serializer = RegionSerializer(region, partial=True, context={'request': request})
        return response.Response(serializer.data)


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


class AdminLevelViewSet(viewsets.ModelViewSet):
    """
    Admin Level API Point
    """
    serializer_class = AdminLevelSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filterset_class = AdminLevelFilterSet
    search_fields = ('title')

    def get_queryset(self):
        return AdminLevel.get_for(self.request.user).select_related('geo_shape_file').defer(
            *AdminLevelSerializer.Meta.exclude
        )


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

        if not admin_level.geojson_file:
            admin_level.calc_cache()

        return redirect(request.build_absolute_uri(admin_level.geojson_file.url))


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

        if not admin_level.bounds_file:
            admin_level.calc_cache()

        return redirect(request.build_absolute_uri(admin_level.bounds_file.url))


class GeoOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        project = request.GET.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.is_member(request.user):
                raise exceptions.PermissionDenied()

        if (
            project.geo_cache_file is None or
            project.geo_cache_hash is None or
            project.geo_cache_hash != hash(tuple(project.regions.order_by('id').values_list('cache_index', flat=True)))
        ):
            generate_project_geo_region_cache(project)
        return redirect(
            request.build_absolute_uri(
                project.geo_cache_file.url
            )
        )


class GeoAreaView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    serializer_class = GeoAreaSerializer
    filterset_class = GeoAreaFilterSet

    def get_queryset(self):
        return GeoArea.objects.filter(
            admin_level__region__project=self.kwargs['project_id'],
            admin_level__region__is_published=True
        ).annotate(
            label=models.functions.Concat(
                models.F('admin_level__title'),
                models.Value('/'),
                models.F('title'),
                output_field=models.fields.CharField()
            ),
            region=models.F('admin_level__region_id'),
            region_title=models.F('admin_level__region__title'),
            admin_level_level=models.F('admin_level__level'),
            admin_level_title=models.F('admin_level__title'),
            key=models.F('id')
        ).distinct()
