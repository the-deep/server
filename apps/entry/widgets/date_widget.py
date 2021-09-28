from datetime import datetime

from analysis_framework.widgets.date_widget import WIDGET_ID


ONE_DAY = 24 * 60 * 60
# NOTE: Please update the data version when you update the data format
# this is tallied against the version stored in the export json data
DATA_VERSION = 1


def _get_date(widget, data, widget_properties):
    value = data.get('value')

    date = value and datetime.strptime(value, '%Y-%m-%d')
    number = date and int(date.timestamp() / ONE_DAY)
    # NOTE: Please update the data version when you update the data format
    return date and date.strftime('%d-%m-%Y'), number


def update_attribute(widget, data, widget_properties):
    date, number = _get_date(widget, data, widget_properties)

    return {
        # NOTE: Please update the data version when you update the data format
        'filter_data': [{
            'number': number,
        }],

        'export_data': {
            'data': {
                'common': {
                    'value': date,
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                },
                'report': {
                }
            }
        },
    }


def get_comprehensive_data(_, *args):
    return _get_date(*args)[0]
