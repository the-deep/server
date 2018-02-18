from .utils import set_filter_data, set_export_data


def update_attribute(entry, widget, data, widget_data):
    value = data.get('value')

    set_filter_data(
        entry,
        widget,
        number=value,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'value': value and str(value),
            },
        },
    )
