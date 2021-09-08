from datetime import datetime

from analysis_framework.widgets.date_range_widget import WIDGET_ID


ONE_DAY = 24 * 60 * 60
# NOTE: Please update the data version when you update the data format
DATA_VERSION = 1


def _get_date(widget, data, widget_data):
    value = data.get('value', {})
    from_value = value.get('from')
    to_value = value.get('to')

    from_date = from_value and datetime.strptime(from_value, '%Y-%m-%d')
    to_date = to_value and datetime.strptime(to_value, '%Y-%m-%d')

    from_number = from_date and int(from_date.timestamp() / ONE_DAY)
    to_number = to_date and int(to_date.timestamp() / ONE_DAY)

    # NOTE: Please update the data version when you update the data format
    return (
        from_number,
        to_number,
    ), (
        from_date and from_date.strftime('%d-%m-%Y'),
        to_date and to_date.strftime('%d-%m-%Y'),
    )


def update_attribute(widget, data, widget_data):
    (from_number, to_number), (from_date, to_date) = _get_date(widget, data, widget_data)

    return {
        # NOTE: Please update the data version when you update the data format
        'filter_data': [{
            'from_number': from_number,
            'to_number': to_number,
        }],

        'export_data': {
            'data': {
                'common': {
                    'values': [from_date, to_date],
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                },
                'report': {
                }
            },
        },
    }


def get_comprehensive_data(_, *args):
    (from_date, to_date) = _get_date(*args)[1]
    return {
        'from': from_date,
        'to': to_date,
    }
