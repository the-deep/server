def _get_number(widget, data, widget_data):
    value = data.get('value')
    return value and str(value), value


def update_attribute(*args):
    str_value, value = _get_number(*args)

    return {
        'filter_data': [{
            'number': value,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': str_value,
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    return _get_number(*args)[0]
