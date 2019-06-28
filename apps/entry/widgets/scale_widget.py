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
                    # TODO: Add migration for this fix (for using get('label'))
                    'value': scale_label,
                },
            },
        },
    }


def get_comprehensive_data(widget, data, widget_data):
    label, selected_scales = _get_scale_label(widget, data, widget_data)
    scale_units = widget_data.get('scale_units', [])
    return {
        'min': scale_units[0] if scale_units else None,
        'max': scale_units[len(scale_units) - 1] if scale_units else None,
        'label': label,
        'index': ([
            (i + 1) for i, v in enumerate(scale_units)
            if v['key'] == selected_scales[0]
        ] or [None])[0] if selected_scales else None,
    }
