def migrate_widget(widget_data):
    return widget_data


def migrate_attribute(data):
    if data.get('value'):
        return data

    return {
        'value': data
    }
