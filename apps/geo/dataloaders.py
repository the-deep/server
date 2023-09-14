from collections import defaultdict
from graphene.types import context

from promise import Promise
from django.utils.functional import cached_property
from django.db.models import Prefetch

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin
from geo.schema import get_geo_area_queryset_for_project_geo_area_type

from .models import AdminLevel, GeoArea
from assessment_registry.models import AssessmentRegistry


class AdminLevelLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        adminlevel_qs = AdminLevel.objects.filter(region__in=keys).defer('geo_area_titles')
        _map = defaultdict(list)
        for adminlevel in adminlevel_qs:
            _map[adminlevel.region_id].append(adminlevel)
        return Promise.resolve([_map.get(key) for key in keys])


class AssessmentRegistryGeoAreaLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        ary_geo_area_qs = AssessmentRegistry.locations.through.objects\
            .filter(assessmentregistry__in=keys).prefetch_related(
                Prefetch('geoarea', queryset=get_geo_area_queryset_for_project_geo_area_type())
            )
        _map = defaultdict(list)
        for ary_geo_area in ary_geo_area_qs.all():
            _map[ary_geo_area.assessmentregistry_id].append(ary_geo_area.geoarea)
        return Promise.resolve([_map.get(key) for key in keys])


class GeoAreaLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        geo_area_qs = GeoArea.objects.filter(id__in=keys).defer('polygons')
        _map = defaultdict()
        for geo_area in geo_area_qs:
            _map[geo_area.id] = geo_area
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def admin_levels_by_region(self):
        return AdminLevelLoader(context=self.context)

    @cached_property
    def assessment_registry_locations(self):
        return AssessmentRegistryGeoAreaLoader(context=self.context)

    @cached_property
    def geo_area(self):
        return GeoAreaLoader(context=self.context)
