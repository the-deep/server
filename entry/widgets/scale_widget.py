from .utils import set_filter_data, set_export_data


def update_attribute(entry, widget, data, widget_data):
    selected_scale = data.get('selected_scale')

    scale_units = widget_data.get('scale_units', [])
    scale = next((
        s for s in scale_units
        if s['key'] == selected_scale
    ), None)

    set_filter_data(
        entry,
        widget,
        values=[selected_scale],
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'value': scale.get('title') if scale else '',
            },
        },
    )
