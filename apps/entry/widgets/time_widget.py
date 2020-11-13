WIDGET_ID = 'timeWidget'

def parse_time(time_string):
    splits = time_string.split(':')
    h = int(splits[0])
    m = int(splits[1])
    return {
        'time_str': '{:02d}:{:02d}'.format(h, m),
        'time_val': h * 60 + m,
    }


def _get_time(widget, data, widget_data):
    value = data.get('value')
    time = value and parse_time(value)
    return time and time['time_val'], value and time['time_str']


def update_attribute(widget, data, widget_data):
    time_val, time_str = _get_time(widget, data, widget_data)

    return {
        'filter_data': [{
            'number': time_val
        }],

        'export_data': {
            'data': {
                'version': 1,
                'common': {
                    'value': time_str,
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key
                },
                'excel': {
                },
                'report': {
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    return _get_time(*args)[1]
