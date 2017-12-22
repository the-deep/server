from celery import shared_task
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import (
    GEOSGeometry,
    MultiPolygon,
)
from django.db.models import Q
from geo.models import Region, AdminLevel, GeoArea

from redis_store import redis

import reversion
import os


@shared_task
def add(x, y):
    """
    Simple task for sole purpose testing celery
    Used in geo.tests.test_celery module
    """
    return x + y


def _save_geo_area(admin_level, parent, feature):
    name = None
    code = None

    if admin_level.name_prop:
        name = feature.get(admin_level.name_prop)
    if admin_level.code_prop:
        code = feature.get(admin_level.code_prop)

    geo_area = GeoArea.objects.filter(
        Q(code=None, title=name) | Q(code=code),
        admin_level=admin_level,
    ).first()

    if not geo_area:
        geo_area = GeoArea()

    geo_area.title = name
    geo_area.code = code if code else name
    geo_area.admin_level = admin_level

    geom = feature.geom
    geom = GEOSGeometry(geom.wkt).simplify(
        tolerance=admin_level.tolerance,
        preserve_topology=True,
    )

    if geom.geom_type == 'Polygon':
        geom = MultiPolygon(geom)
    elif geom.geom_type != 'MultiPolygon':
        raise Exception('Invalid geometry type for geoarea')

    geo_area.polygons = geom

    if parent:
        if admin_level.parent_name_prop:
            candidates = GeoArea.objects.filter(
                admin_level=parent,
                title=feature.get(admin_level.parent_name_prop)
            )

            if admin_level.parent_code_prop:
                candidates = candidates.filter(
                    code=feature.get(admin_level.parent_code_prop)
                )
            geo_area.parent = candidates.first()

        elif admin_level.parent_code_prop:
            geo_area.parent = GeoArea.objects.filter(
                admin_level=parent,
                code=feature.get(admin_level.parent_code_prop)
            ).first()

    geo_area.save()
    return geo_area


def _load_geo_areas(region_id):
    """
    The main load geo areas procedure

    Basically, it  starts with root admin level and iterate through all the
    children.
    """

    with reversion.create_revision():
        region = Region.objects.get(pk=region_id)

        if AdminLevel.objects.filter(region=region).count() == 0:
            return

        admin_level = AdminLevel.objects.filter(region=region, parent=None)\
            .first()
        parent = None

        # TODO: Check for cycle and for admin levels
        # with no parent
        while admin_level:
            geo_shape_file = admin_level.geo_shape_file
            if geo_shape_file:
                data_source = DataSource(os.path.join(
                    settings.MEDIA_ROOT,
                    geo_shape_file.file.name
                ))
                if data_source.layer_count == 1:
                    layer = data_source[0]

                    added_areas = []
                    for feature in layer:
                        geo_area = _save_geo_area(
                            admin_level, parent,
                            feature
                        )
                        added_areas.append(geo_area.id)

                    GeoArea.objects.filter(
                        admin_level=admin_level
                    ).exclude(id__in=added_areas).delete()

            admin_level.stale_geo_areas = False
            admin_level.save()

            parent = admin_level
            admin_level = AdminLevel.objects.filter(parent=parent).first()

    return True


@shared_task
def load_geo_areas(region_id):
    r = redis.get_connection()
    key = 'load_geo_areas_{}'.format(region_id)
    lock = 'lock_{}'.format(key)

    with redis.get_lock(lock):
        if r.exists(key):
            return False
        r.set(key, '1')

    try:
        return_value = _load_geo_areas(region_id)
    except Exception:
        return_value = False

    r.delete(key)
    return return_value
