from celery import shared_task
from django.conf import settings
from django.contrib.gis.gdal import (
    DataSource,
    OGRGeomType,
    OGRGeometry
)
from django.db.models import Q
from geo.models import Region, AdminLevel, GeoArea

import reversion
import os


@shared_task
def add(x, y):
    return x + y


def save_geo_area(admin_level, parent, feature):
    name = None
    code = None

    if admin_level.name_prop:
        name = feature.get(admin_level.name_prop)
    if admin_level.code_prop:
        code = feature.get(admin_level.code_prop)

    geo_area = GeoArea.objects.filter(
        Q(code=None) | Q(code=code),
        title=name,
        admin_level=admin_level,
    ).first()

    if not geo_area:
        geo_area = GeoArea()

    geo_area.title = name
    geo_area.code = code
    geo_area.admin_level = admin_level

    geom = feature.geom
    if geom.geom_type == OGRGeomType('Polygon'):
        g = OGRGeometry(OGRGeomType('MultiPolygon'))
        g.add(geom)
        geom = g
    elif geom.geom_type != OGRGeomType('MultiPolygon'):
        raise Exception('Invalid geometry type for geoarea')
    geo_area.polygons = geom.wkt

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


@shared_task
def load_geo_areas(region_id):
    """
    A task to auto load geo areas from all admin levels in a region/country.

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
                        geo_area = save_geo_area(admin_level, parent, feature)
                        added_areas.append(geo_area.id)

                    GeoArea.objects.filter(
                        admin_level=admin_level
                    ).exclude(id__in=added_areas).delete()

            parent = admin_level
            admin_level = AdminLevel.objects.filter(parent=parent).first()

    return True
