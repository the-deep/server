def _get_scale_label(widget, data, widget_data):
    selected_scale = data.get('value')
    selected_scales = [selected_scale] if selected_scale is not None else []

    scale_units = widget_data.get('scale_units', [])
    scale = next((
        s for s in scale_units
        if s['key'] == selected_scale
    ), None)
    return scale.get('label') if scale else None, selected_scales


def update_attribute(widget, data, widget_data):
    scale_label, selected_scales = _get_scale_label(widget, data, widget_data)

    return {
        'filter_data': [{
            'values': selected_scales,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': scale_label,
                },
            },
        },
    }


def get_comprehensive_data(*args):
    return _get_scale_label(*args)[0]
