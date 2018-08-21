def migrate_widget(widget_data):
    units = widget_data.get('scale_units') or []
    for unit in units:
        unit['label'] = unit['title']
        unit.pop('title')
    return widget_data


def migrate_attribute(data):
    return {
        'value': data.get('selected_scale')
    }
