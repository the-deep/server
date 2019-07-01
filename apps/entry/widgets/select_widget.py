def _get_label_list(widget, data, widget_data):
    values = data.get('value')
    values = [values] if values is not None else []

    options = widget_data.get('options', [])
    label_list = []
    for item in values:
        option = next((
            o for o in options
            if o.get('key') == item
        ), None)
        if option:
            label_list.append(option.get('label') or 'Unknown')

    return label_list, values


def update_attribute(widget, data, widget_data):
    label_list, values = _get_label_list(widget, data, widget_data)

    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'type': 'list',
                    'value': label_list,
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    label_list = _get_label_list(*args)[0]
    if label_list:
        return label_list[0]
