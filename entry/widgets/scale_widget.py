def update_attribute(widget, data, widget_data):
    selected_scale = data.get('value')

    scale_units = widget_data.get('scale_units', [])
    scale = next((
        s for s in scale_units
        if s['key'] == selected_scale
    ), None)

    return {
        'filter_data': [{
            'values': [selected_scale],
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': scale.get('title') if scale else '',
                },
            },
        },
    }
