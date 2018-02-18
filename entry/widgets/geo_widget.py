from .utils import set_filter_data, set_export_data


def update_attribute(entry, widget, data, widget_data):
    values = data.get('values', [])
    keys = [str(v.get('key', '')) for v in values]

    set_filter_data(
        entry,
        widget,
        values=keys,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'values': keys,
            },
        },
    )
