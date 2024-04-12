from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property
from django.db.models import Prefetch
from assisted_tagging.models import DraftEntry

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin
from geo.schema import get_geo_area_queryset_for_project_geo_area_type

from .models import AdminLevel
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


class DraftEntryGeoAreaLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        draft_entry_geo_area_qs = DraftEntry.objects\
            .filter(id__in=keys).prefetch_related(
                Prefetch('related_geoareas', queryset=get_geo_area_queryset_for_project_geo_area_type())
            ).only('pk')
        _map = defaultdict(list)
        for draft_entry_geo_area in draft_entry_geo_area_qs.all():
            _map[draft_entry_geo_area.pk].extend(draft_entry_geo_area.related_geoareas.all())
        return Promise.resolve([_map.get(key, []) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def admin_levels_by_region(self):
        return AdminLevelLoader(context=self.context)

    @cached_property
    def assessment_registry_locations(self):
        return AssessmentRegistryGeoAreaLoader(context=self.context)

    @cached_property
    def draft_entry_geo_area(self):
        return DraftEntryGeoAreaLoader(context=self.context)
