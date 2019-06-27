from datetime import datetime


ONE_DAY = 24 * 60 * 60


def _get_date(widget, data, widget_data):
    value = data.get('value')

    date = value and datetime.strptime(value, '%Y-%m-%d')
    number = date and int(date.timestamp() / ONE_DAY)
    return date and date.strftime('%d-%m-%Y'), number


def update_attribute(widget, data, widget_data):
    date, number = _get_date(widget, data, widget_data)

    return {
        'filter_data': [{
            'number': number,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': date,
                },
            }
        },
    }


def get_comprehensive_data(*args):
    return _get_date(*args)[0]
