def migrate_widget(widget_data):
    return widget_data


def migrate_attribute(data):
    value = data.get('values') or []
    return {
        'value': [v['id'] for v in value],
    }
