def update_attribute(widget, data, widget_data):
    value = data.get('value')

    return {
        'filter_data': [{
            'number': value,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': value and str(value),
                },
            },
        },
    }
