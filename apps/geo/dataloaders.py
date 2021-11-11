from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    AdminLevel,
)


class AdminLevelLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        adminlevel_qs = AdminLevel.objects.filter(region__in=keys).defer('geo_area_titles')
        _map = defaultdict(list)
        for adminlevel in adminlevel_qs:
            _map[adminlevel.region_id].append(adminlevel)
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def admin_levels_by_region(self):
        return AdminLevelLoader(context=self.context)
