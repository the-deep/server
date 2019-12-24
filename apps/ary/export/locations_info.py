from apps.entry.widgets.geo_widget import get_valid_geo_ids
from geo.models import GeoArea

default_values = {
}


def get_locations_info(assessment):
    locations = get_valid_geo_ids(assessment.methodology['locations']) or []

    geo_areas = GeoArea.objects.filter(id__in=locations).prefetch_related('admin_level', 'parent')

    data = []

    if not geo_areas:
        return {'locations': data}

    # Region is the region of the first geo area
    region = geo_areas[0].admin_level.region
    region_geos = {x['key']: x for x in region.geo_options}

    for area in geo_areas:
        geo_info = region_geos.get(str(area.id))
        if geo_info is None:
            continue
        level = geo_info['admin_level']
        key = f'Admin {level}'

        admin_levels = {f'Admin {x}': None for x in range(7)}
        admin_levels[key] = area.title
        # Now add parents as well
        while level - 1:
            level -= 1
            parent_id = geo_info['parent']

            if parent_id is None:
                break

            geo_info = region_geos.get(str(parent_id))
            if not geo_info:
                break

            key = f'Admin {level}'
            admin_levels[key] = geo_info['title']
        data.append(admin_levels)

    return {
        'locations': data,
    }
