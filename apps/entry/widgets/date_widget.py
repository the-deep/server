from datetime import datetime


ONE_DAY = 24 * 60 * 60


def update_attribute(widget, data, widget_data):
    value = data.get('value')

    date = value and datetime.strptime(value, '%Y-%m-%d')
    number = date and int(date.timestamp() / ONE_DAY)

    return {
        'filter_data': [{
            'number': number,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': date and date.strftime('%d-%m-%Y'),
                },
            }
        },
    }
