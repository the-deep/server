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
