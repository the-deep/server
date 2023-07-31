from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property
from django.db import connection as django_db_connection

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Region,
    AdminLevel,
    GeoArea,
)


class AdminLevelLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        adminlevel_qs = AdminLevel.objects.filter(region__in=keys).defer('geo_area_titles')
        _map = defaultdict(list)
        for adminlevel in adminlevel_qs:
            _map[adminlevel.region_id].append(adminlevel)
        return Promise.resolve([_map.get(key) for key in keys])


class GeoAreaParentsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        def _get_all_parent_node(parent_id, all_geo_areas_dict):
            if parent_id is None or parent_id not in all_geo_areas_dict:
                return
            parent = all_geo_areas_dict[parent_id]
            childs = _get_all_parent_node(parent['parent_id'], all_geo_areas_dict)
            if childs is not None:
                return [
                    parent,
                    *childs,
                ]
            return [parent]

        # NOTE: keys will include parent_ids of the requested geoarea
        with django_db_connection.cursor() as cursor:
            raw_sql = f'''
              WITH RECURSIVE parents AS (
               SELECT
                g.id,
                g.title,
                g.parent_id,
                AL.level,
                AL.title,
                R.title
               FROM {GeoArea._meta.db_table} g
                 INNER JOIN {AdminLevel._meta.db_table} AS AL ON AL.id = g.admin_level_id
                 INNER JOIN {Region._meta.db_table} AS R ON R.id = AL.region_id
               WHERE g.id in %(geo_area_ids)s
               UNION
               SELECT
                t.id,
                t.title,
                t.parent_id,
                tAL.level,
                tAL.title,
                tR.title
               FROM {GeoArea._meta.db_table} AS t
                 INNER JOIN parents AS p ON t.id = p.parent_id
                 INNER JOIN {AdminLevel._meta.db_table} AS tAL ON tAL.id = admin_level_id
                 INNER JOIN {Region._meta.db_table} AS tR ON tR.id = tAL.region_id
              ) SELECT * FROM parents ORDER BY level;
            '''
            cursor.execute(raw_sql, {'geo_area_ids': tuple(keys)})
            geo_area_data = {
                id: {
                    'id': id,
                    'title': title,
                    'parent_id': parent_id,
                    'region_title': region_title,
                    'admin_level_title': admin_level_title,
                    'admin_level_level': admin_level_level,
                }
                for id, title, parent_id, admin_level_level, admin_level_title, region_title in cursor.fetchall()
            }
        return Promise.resolve([_get_all_parent_node(key, geo_area_data) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def admin_levels_by_region(self):
        return AdminLevelLoader(context=self.context)

    @cached_property
    def geo_area_parents(self):
        return GeoAreaParentsLoader(context=self.context)
