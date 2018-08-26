from .utils import set_filter_data, set_export_data


def parse_time(time_string):
    splits = time_string.split(':')
    h = int(splits[0])
    m = int(splits[1])
    return {
        'time_str': '{:02d}:{:02d}'.format(h, m),
        'time_val': h * 60 + m,
    }


def update_attribute(entry, widget, data, widget_data):
    value = data.get('value')
    time = value and parse_time(value)

    number = time and time['time_val']
    set_filter_data(
        entry,
        widget,
        number=number,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'value': time and time['time_str'],
            },
        },
    )
