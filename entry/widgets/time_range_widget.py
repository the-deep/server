def parse_time(time_string):
    splits = time_string.split(':')
    h = int(splits[0])
    m = int(splits[1])
    return {
        'time_str': '{:02d}:{:02d}'.format(h, m),
        'time_val': h * 60 + m,
    }


def update_attribute(widget, data, widget_data):
    from_value = data.get('from_value')
    to_value = data.get('to_value')

    from_time = from_value and parse_time(from_value)
    to_time = to_value and parse_time(to_value)

    return {
        'filter_data': [{
            'from_number': from_time and from_time['time_val'],
            'to_number': to_time and to_time['time_val'],
        }],

        'export_data': {
            'data': {
                'excel': {
                    'values': [
                        from_time and from_time['time_str'],
                        to_time and to_time['time_str'],
                    ],
                },
            },
        },
    }
