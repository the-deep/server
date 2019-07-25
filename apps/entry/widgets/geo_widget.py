def update_attribute(widget, data, widget_data):
    values = data.get('value', [])
    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'values': values,
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

    geo_areas_id = (data or {}).get('value') or []

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
