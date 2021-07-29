from analysis_framework.widgets.number_widget import WIDGET_ID


DATA_VERSION = 1


def _get_number(widget, data, widget_data):
    value = data.get('value')
    return value and str(value), value


def update_attribute(*args):
    str_value, value = _get_number(*args)
    widget = args[0]

    return {
        'filter_data': [{
            'number': value,
        }],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'value': str_value,
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    return _get_number(*args)[0]
