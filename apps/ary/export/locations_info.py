from geo.models import GeoArea

default_values = {
}


def get_locations_info(assessment):
    locations = assessment.methodology['locations'] or []

    geo_areas = GeoArea.objects.filter(id__in=locations).prefetch_related('admin_level', 'parent')

    data = []

    if not geo_areas:
        return {'locations': data}

    # Region is the region of the first geo area
    region = geo_areas[0].admin_level.region
    region_geos = {x['key']: x for x in region.geo_options}

    for area in geo_areas:
        geo_info = region_geos[str(area.id)]
        level = geo_info['admin_level']
        key = f'Admin {level}'

        admin_levels = {f'Admin {x+1}': None for x in range(6)}
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
