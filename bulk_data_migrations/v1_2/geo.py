def migrate_widget(widget_data):
    return widget_data


def migrate_val(v):
    if isinstance(v, dict):
        return v['key']
    return v


def migrate_attribute(data):
    value = data.get('values') or []
    return {
        'value': [migrate_val(v) for v in value],
    }
