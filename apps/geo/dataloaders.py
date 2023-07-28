from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    AdminLevel,
)
from assessment_registry.models import AssessmentRegistry


class AdminLevelLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        adminlevel_qs = AdminLevel.objects.filter(region__in=keys).defer('geo_area_titles')
        _map = defaultdict(list)
        for adminlevel in adminlevel_qs:
            _map[adminlevel.region_id].append(adminlevel)
        return Promise.resolve([_map.get(key) for key in keys])


class GeoAreaLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        ary_geo_area_qs = AssessmentRegistry.locations.through.objects\
            .filter(assessmentregistry__in=keys).prefetch_related('geoarea')
        _map = defaultdict(list)
        for ary_geo_area in ary_geo_area_qs.all():
            _map[ary_geo_area.assessmentregistry_id].append(ary_geo_area.geoarea)
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def admin_levels_by_region(self):
        return AdminLevelLoader(context=self.context)

    @cached_property
    def assessment_registry_locations(self):
        return GeoAreaLoader(context=self.context)
