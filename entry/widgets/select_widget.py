def update_attribute(widget, data, widget_data):
    value = data.get('value')
    value = [value] if value is not None else []

    options = widget_data.get('options', [])
    label_list = []
    for item in value:
        option = next((
            o for o in options
            if o.get('key') == item
        ), None)
        label_list.append(option.get('label') or 'Unknown')

    return {
        'filter_data': [{
            'values': value,
        }],

        'exportable': {
            'data': {
                'excel': {
                    'type': 'list',
                    'value': label_list,
                },
            },
        },
    }
