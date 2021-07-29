from analysis_framework.widgets.multiselect_widget import WIDGET_ID


# NOTE: Please update the data version when you update the data format
DATA_VERSION = 1


def _get_label_list(widget, data, widget_data):
    values = data.get('value', [])
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
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                    'type': 'list',
                    'value': label_list,
                },
                'excel': {
                },
            }
        },
    }


def get_comprehensive_data(_, *args):
    return _get_label_list(*args)[0]
