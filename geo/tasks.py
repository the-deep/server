from celery import shared_task
from django.db.models import Q
from geo.models import AdminLevel, GeoArea


@shared_task
def add(x, y):
    return x + y


@shared_task
def load_geoareas(region):
    """
    A task to auto load geo areas from all admin levels in a region/country.

    Basically, it  starts with root admin level and iterate through all the
    children.

    For each admin level, it gets the name and code of each feature.
    It either searches an old geo area with same name and code or creates a
    new one. Then it tries to find appropriate parent for the geo area with
    parent's name and code.
    """

    if AdminLevel.objects.filter(region=region).count() == 0:
        return

    admin_level = AdminLevel.objects.get(region=region, parent=None)
    parent = None
    while admin_level:

        geo_shape = admin_level.geo_shape
        if geo_shape is None:
            continue

        features = geo_shape['features']
        for feature in features:
            props = feature['properties']

            name = None
            code = None

            if admin_level.name_prop:
                name = props[admin_level.name_prop]
            if admin_level.code_prop:
                code = props[admin_level.code_prop]

            geo_area = GeoArea.objects.filter(
                Q(code=None) | Q(code=code),
                name=name,
                admin_level=admin_level,
            ).first()

            if not geo_area:
                geo_area = GeoArea()

            geo_area.name = name
            geo_area.code = code

            if parent:
                if admin_level.parent_name_prop:
                    candidates = GeoArea.objects.filter(
                        admin_level=parent,
                        name=props[admin_level.parent_name_prop]
                    )

                    if admin_level.pareant_code_prop:
                        candidates = candidates.filter(
                            code=props[admin_level.parent_code_prop]
                        )

                    geo_area.parent = candidates.first()

            geo_area.save()

        parent = admin_level
        admin_level = AdminLevel.objects.filter(parent=parent).first()
