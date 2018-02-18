from .utils import set_filter_data, set_export_data


def update_attribute(entry, widget, data, widget_data):
    value = data.get('value', [])

    set_filter_data(
        entry,
        widget,
        values=value,
    )

    options = widget_data.get('options', [])
    label_list = []
    for item in value:
        option = next((
            o for o in options
            if o.get('key') == item
        ), None)
        label_list.append(option.get('label') or 'Unknown')

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'type': 'list',
                'value': label_list,
            },
        },
    )
