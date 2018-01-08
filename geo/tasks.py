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

import os
import reversion
import tempfile

import traceback
import logging

logger = logging.getLogger(__name__)


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


def _generate_geo_areas(admin_level, parent):
    # Get the geo shape file
    geo_shape_file = admin_level.geo_shape_file
    if geo_shape_file:
        # Create temporary file with same content
        # This is necessary in server where the file is
        # originally in s3 server and GDAL expects file in local
        # disk.

        # Then load data from that file
        filename, extension = os.path.splitext(geo_shape_file.file.name)
        f = tempfile.NamedTemporaryFile(suffix=extension,
                                        dir=settings.BASE_DIR)
        f.write(geo_shape_file.file.read())
        data_source = DataSource(f.name)
        f.close()

        # If more than one layer exists, extract from the first layer
        if data_source.layer_count == 1:
            layer = data_source[0]

            added_areas = []
            for feature in layer:
                # Each feature is a geo area
                geo_area = _save_geo_area(
                    admin_level, parent,
                    feature,
                )
                added_areas.append(geo_area.id)

            # Delete all previous geo areas that have not been added
            GeoArea.objects.filter(
                admin_level=admin_level
            ).exclude(id__in=added_areas).delete()

    admin_level.stale_geo_areas = False
    admin_level.save()


def _extract_from_admin_levels(admin_levels, parent, completed_levels):
    for admin_level in admin_levels:
        # Cyclic check
        if admin_level.id in completed_levels:
            continue
        completed_levels.append(admin_level.id)

        # Generate geo areas
        _generate_geo_areas(admin_level, parent)

        # Extract children areas
        children_levels = AdminLevel.objects.filter(parent=admin_level)
        if children_levels.count() > 0:
            _extract_from_admin_levels(
                children_levels,
                admin_level,
                completed_levels,
            )


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

        parent_admin_levels = AdminLevel.objects.filter(
            region=region, parent=None
        )
        completed_levels = []
        _extract_from_admin_levels(
            parent_admin_levels,
            None,
            completed_levels,
        )

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
        logger.error(traceback.format_exc())
        return_value = False

    r.delete(key)
    return return_value
