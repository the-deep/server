def migrate_widget(widget_data):
    units = widget_data.get('scale_units') or []
    for unit in units:
        if unit.get('title'):
            unit['label'] = unit['title']
            unit.pop('title')
    return widget_data


def migrate_attribute(data):
    if data.get('value'):
        return data

    return {
        'value': data.get('selected_scale')
    }
