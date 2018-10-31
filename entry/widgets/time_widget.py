def parse_time(time_string):
    splits = time_string.split(':')
    h = int(splits[0])
    m = int(splits[1])
    return {
        'time_str': '{:02d}:{:02d}'.format(h, m),
        'time_val': h * 60 + m,
    }


def update_attribute(widget, data, widget_data):
    value = data.get('value')
    time = value and parse_time(value)

    number = time and time['time_val']

    return {
        'filter_data': [{
            'number': number,
        }],

        'exportable': {
            'data': {
                'excel': {
                    'value': time and time['time_str'],
                },
            },
        },
    }
