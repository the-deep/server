from analysis_framework.widgets.time_range_widget import WIDGET_ID
from .time_widget import parse_time_str


# NOTE: Please update the data version when you update the data format
DATA_VERSION = 1


def _get_time(widget, data, widget_properties):
    value = data.get('value') or {}
    from_value = value.get('startTime')  # TODO: use from
    to_value = value.get('endTime')  # TODO: use to

    from_time = from_value and parse_time_str(from_value)
    to_time = to_value and parse_time_str(to_value)
    # NOTE: Please update the data version when you update the data format
    return (
        from_time and from_time['time_val'],
        to_time and to_time['time_val'],
    ), (
        from_time and from_time['time_str'],
        to_time and to_time['time_str'],
    )


def update_attribute(widget, data, widget_properties):
    (
        from_number,
        to_number,
    ), (
        from_time,
        to_time,
    ) = _get_time(widget, data, widget_properties)

    return {
        # NOTE: Please update the data version when you update the data format
        'filter_data': [{
            'from_number': from_number,
            'to_number': to_number,
        }],

        'export_data': {
            'data': {
                'common': {
                    'values': [from_time, to_time],
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                },
                'report': {
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    (from_time, to_time) = _get_time(*args)[1]
    return {
        'from': from_time,
        'to': to_time,
    }
