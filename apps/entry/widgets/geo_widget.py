from utils.common import is_valid_number

WIDGET_ID = 'geoWidget'
DATA_VERSION = 1


def _get_geoareas_from_polygon(geo_value):
    try:
        properties = geo_value['geo_json']['properties']
        return properties['geoareas'], properties.get('title'), geo_value['region']
    except (AttributeError, KeyError):
        return [], None, None


def get_valid_geo_ids(raw_values, extract_polygon_title=False):
    """
    Geo values can have {}, Number, String values
    Only Number, String(convertable to integer) values are valid
    Also extract from polygons
    """
    geo_areas = []
    polygons = []

    for raw_value in raw_values:
        if is_valid_number(raw_value):
            geo_areas.append(int(raw_value))
        else:
            # This will be a polygon
            pgeo_areas, ptitle, pregion_id = _get_geoareas_from_polygon(raw_value)
            geo_areas.extend([
                int(id) for id in pgeo_areas if is_valid_number(id)
            ])
            if extract_polygon_title and ptitle and pregion_id:
                polygons.append({
                    'region_id': pregion_id,
                    'title': ptitle,
                })

    geo_areas = list(set(geo_areas))
    if extract_polygon_title:
        return geo_areas, polygons
    return geo_areas


def update_attribute(widget, data, widget_data):
    values, polygons = get_valid_geo_ids(
        data.get('value') or [],
        extract_polygon_title=True,
    )

    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                    'values': values,  # GEOAREA IDs
                },
                'excel': {
                    'polygons': polygons,  # Polygons
                },
            }
        },
    }


def _get_geo_area_parents(geo_areas, admin_levels, geo_area):
    parent = geo_areas.get(geo_area['parent'])
    if parent is None:
        return []

    parents = [{
        'id': parent['id'],
        'title': parent['title'],
        'pcode': parent['pcode'],
        'admin_level': admin_levels.get(parent['admin_level']),
    }]
    p_parent = geo_areas.get(parent.get('parent'))
    if p_parent:
        parents.extend(
            _get_geo_area_parents(geo_areas, admin_levels, p_parent)
        )
    return parents


def get_comprehensive_data(widgets_meta, widget, data, widget_data):
    geo_areas = widgets_meta['geo-widget']['geo_areas']
    admin_levels = widgets_meta['geo-widget']['admin_levels']

    # Ignore invalid ids
    geo_areas_id = get_valid_geo_ids((data or {}).get('value') or [])

    values = []

    for geo_area_id in geo_areas_id:
        geo_area = geo_areas.get(int(geo_area_id))
        if geo_area is None:
            continue
        admin_level = admin_levels.get(geo_area.get('admin_level'))
        values.append({
            'id': geo_area['id'],
            'title': geo_area['title'],
            'pcode': geo_area['pcode'],
            'admin_level': admin_level,
            'parent': _get_geo_area_parents(geo_areas, admin_levels, geo_area),
        })

    return values or geo_areas_id
